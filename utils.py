import math
import datetime
from logger import debug, info, warning, error

def SM2(quality, repetitions, previous_ease_factor, previous_interval):
    info(f"SM2 called: quality={quality}, repetitions={repetitions}, ease_factor={previous_ease_factor:.3f}, interval={previous_interval}")

    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 4
        else:
            interval = previous_interval * previous_ease_factor
            interval = math.ceil(interval)
        repetitions += 1
        ease_factor = previous_ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ease_factor = max(ease_factor, 1.3)
        info(f"SM2 success (>=3): new_interval={interval}, new_repetitions={repetitions}, new_ease_factor={ease_factor:.3f}")
        return interval, repetitions, ease_factor
    else:
        interval = 1
        repetitions = 0
        #ease_factor = previous_ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        ease_factor = previous_ease_factor
        ease_factor = max(ease_factor, 1.3)
        info(f"SM2 failure (<3): reset to interval=1, repetitions=0, new_ease_factor={ease_factor:.3f}")
        return interval, repetitions, ease_factor