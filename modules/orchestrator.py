# orchestrator.py
import queue
import threading
import time
import signal

try:
    from modules.logger import start_logger_thread, info, debug, warn, error
    from modules.sync import file_lock
    import modules.thoughts_goals as tg
    import modules.memory as mem
    import modules.knowledge as kn
    import modules.rewards as rw
    import modules.conversation_style as cs
except ImportError:
    from logger import start_logger_thread, info, debug, warn, error
    from sync import file_lock
    import thoughts_goals as tg
    import memory as mem
    import knowledge as kn
    import rewards as rw
    import conversation_style as cs

# Task priorities: 0=high (interactive), 1=normal (autonomous), 2=low (maintenance)
Task = tuple  # (priority:int, task_id:str, func:callable, kwargs:dict)

TASK_QUEUE = queue.PriorityQueue(maxsize=200)
SHUTDOWN = threading.Event()

# simple generator placeholder (replace with your API call)
def call_model_generate(prompt: str, max_tokens: int = 256, timeout: float = 30.0) -> str:
    """
    Replace this with your actual model call. Timeout must be enforced there.
    This stub simply echos the prompt head for local testing.
    """
    debug("Model generate called but using stub.")
    return "..."  # real implementation goes here


def worker_loop():
    info("Worker loop started.")
    while not SHUTDOWN.is_set():
        try:
            priority, task_id, func, kwargs = TASK_QUEUE.get(timeout=0.5)
        except queue.Empty:
            continue
        try:
            debug(f"Executing task {task_id} (priority {priority})")
            # run task
            func(**(kwargs or {}))
        except Exception as e:
            error(f"Task {task_id} failed: {e}")
        finally:
            TASK_QUEUE.task_done()
    info("Worker loop exiting.")


def schedule_task(func, kwargs=None, priority=1, task_id=None):
    """Enqueue a task. Non-blocking; returns True if scheduled, False if queue full."""
    if task_id is None:
        task_id = f"T{int(time.time()*1000)}"
    try:
        TASK_QUEUE.put_nowait((priority, task_id, func, kwargs or {}))
        return True
    except queue.Full:
        warn("Task queue full; dropping task " + str(task_id))
        return False


# Example task: handle interactive user message
def handle_user_message(user_input: str, user_meta: dict = None):
    """
    1) Sanitize input
    2) Build prompt without logs
    3) Call model (with timeout)
    4) Persist thoughts/memory within file_lock
    5) Push reply to output (here: logger.info) so only logger prints
    """
    debug(f"handle_user_message got input: {user_input[:80]}")
    # Build curated context (no debug logs). Use your memory/knowledge retrievals:
    try:
        # Get similar memories (safe, read-only)
        with file_lock():
            mem_ids = mem.associative_recall(user_input, top_k=3)  # returns list of (id,score)
            knowledge_hits = kn.retrieve_knowledge(user_input, top_k=3)
        # Compose prompt text from those items (but NOT debug logs)
        prompt_parts = ["You are Vashrak. Keep replies short and in conversational style."]
        # include memory summaries
        for mid, _ in mem_ids:
            mi = mem.load_memory_index().get(mid)
            if mi:
                prompt_parts.append(mi.get("summary",""))
        for kid, _ in knowledge_hits:
            idx = kn.load_knowledge_index().get(kid)
            if idx:
                prompt_parts.append(idx.get("summary",""))
        # reward conditioning (short)
        rc = rw.get_reward_conditioning()
        if rc:
            prompt_parts.append(rc)
        prompt_parts.append("User: " + user_input)
        prompt = "\n\n".join(prompt_parts)[:15000]
        # Generate reply
        reply = call_model_generate(prompt, max_tokens=256, timeout=20.0)
    except Exception as e:
        error("Error during user message handling: " + str(e))
        reply = "I don't know."

    # Save thought + working thought under file lock to avoid race
    try:
        with file_lock():
            tg.add_thought(reply)
            tg.add_working_thought("Received input: " + (user_input[:200]))
    except Exception as e:
        warn("Failed to persist thought: " + str(e))

    # Output reply (only logger prints)
    info(f"[Vashrak] {reply}")


# Example autonomous cycle task (lower priority)
def autonomous_cycle():
    debug("Autonomous cycle tick.")
    # Create an internal thought silently (no speech)
    try:
        with file_lock():
            new = tg.add_thought("Autonomous internal reflection (silent).", strength=0.4)
        # schedule low-priority maintenance: rebuild indices later (debounced)
        schedule_task(lambda: kn.rebuild_knowledge_index(), priority=2, task_id="rebuild_knowledge_index")
    except Exception as e:
        warn("Autonomous cycle failed: " + str(e))


# Graceful shutdown
def start_orchestrator():
    start_logger_thread()
    info("Starting orchestrator.")
    # start worker pool
    workers = []
    for i in range(3):
        t = threading.Thread(target=worker_loop, daemon=True, name=f"Worker-{i}")
        t.start()
        workers.append(t)

    # schedule periodic autonomous cycles
    def autonomous_runner():
        while not SHUTDOWN.is_set():
            schedule_task(autonomous_cycle, priority=1, task_id=f"autocycle_{int(time.time())}")
            time.sleep(120)  # config
    ar = threading.Thread(target=autonomous_runner, daemon=True, name="AutonRunner")
    ar.start()

    # hook ctrl+c
    def handle_sigint(sig, frame):
        info("Shutdown signal received.")
        SHUTDOWN.set()
    signal.signal(signal.SIGINT, handle_sigint)

    info("Orchestrator ready.")

if __name__ == "__main__":
    start_orchestrator()
    # Keep main thread alive
    try:
        while not SHUTDOWN.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        SHUTDOWN.set()
    time.sleep(0.5)
    info("Main exit.")
