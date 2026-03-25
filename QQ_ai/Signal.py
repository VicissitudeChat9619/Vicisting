from threading import Semaphore

ai_response_items = Semaphore(0)
ai_response_space = Semaphore(100)
ai_response_lock = Semaphore(1)

user_text_lock = Semaphore(1)

ai_speaker_stop_lock = Semaphore(1)

ai_speaker_stop = 0
