def play_sound(file_path):
    import os
    import time
    os.environ["SDL_AUDIODRIVER"] = "alsa"   
    #os.environ["ALSADEV"] = "hw:0,0" 
    os.environ["AUDIODEV"] = "hw:3,0" 
    import pygame
    pygame.mixer.init(
        buffer=4096     
    )
    print('Should be playing')
    sound = pygame.mixer.Sound(file_path)

    sound.play()

    while pygame.mixer.get_busy():
        time.sleep(0.1)