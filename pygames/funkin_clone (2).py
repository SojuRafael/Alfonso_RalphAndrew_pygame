import pygame
import random
import os
import math

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Funkin Clone")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BG_COLOR = (30, 30, 30)

# Font
font = pygame.font.SysFont("Arial", 36)
title_font = pygame.font.SysFont("Arial", 64, bold=True)
count_font = pygame.font.SysFont("Arial", 96, bold=True)

# Base dir
BASE_DIR = os.path.dirname(__file__)

# --- Image helpers ---
def round_corners(image, radius=12):
    size = image.get_size()
    mask = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, *size), border_radius=radius)
    result = pygame.Surface(size, pygame.SRCALPHA)
    result.blit(image, (0, 0))
    result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return result

def load_and_smooth(path, size, radius=12):
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.smoothscale(img, (size, size))
    img = round_corners(img, radius)
    return img

# --- Load images ---
arrow_size = 80
arrow_images = [
    load_and_smooth(os.path.join(BASE_DIR, "left.png"), arrow_size),
    load_and_smooth(os.path.join(BASE_DIR, "up.png"), arrow_size),    # swapped
    load_and_smooth(os.path.join(BASE_DIR, "down.png"), arrow_size),  # swapped
    load_and_smooth(os.path.join(BASE_DIR, "right.png"), arrow_size)
]
falling_arrow_images = [
    load_and_smooth(os.path.join(BASE_DIR, "left_img.png"), arrow_size),
    load_and_smooth(os.path.join(BASE_DIR, "up_img.png"), arrow_size),    # swapped
    load_and_smooth(os.path.join(BASE_DIR, "down_img.png"), arrow_size),  # swapped
    load_and_smooth(os.path.join(BASE_DIR, "right_img.png"), arrow_size)
]

# --- Main menu background ---
menu_bg = pygame.image.load(os.path.join(BASE_DIR, "FNF wallpaper.jpg")).convert()
menu_bg = pygame.transform.smoothscale(menu_bg, (WIDTH, HEIGHT))

# --- Game background ---
game_bg = pygame.image.load(os.path.join(BASE_DIR, "game_bg.png")).convert()
game_bg = pygame.transform.smoothscale(game_bg, (WIDTH, HEIGHT))

# --- Game settings ---
fall_speed = 7
lanes = [100, 200, 300, 400]
keys = [pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT]  # swapped up and down

score = 0
health = 5

# --- Highscore per difficulty ---
highscore_file = "highscore.txt"
difficulties = ["Easy", "Normal", "Hard"]
highscores = {diff: 0 for diff in difficulties}

# Load highscores from file if it exists
if os.path.exists(highscore_file):
    try:
        with open(highscore_file, "r") as f:
            for line in f:
                diff, val = line.strip().split(":")
                highscores[diff] = int(val)
    except:
        pass

# --- Game over phrases ---
game_over_phrases = [
    "Agay",
    "Akala ko ulan, luha ko pala iyon",
    "SKILL ISSUE!",
    "Hampang nalang snek snek",
    "LMAO"
]
current_game_over_text = "GAME OVER"

# --- Arrow class ---
class Arrow:
    def __init__(self, lane, index):
        self.x = lane
        self.y = -arrow_size
        self.index = index
        self.image = falling_arrow_images[index]
        self.rect = self.image.get_rect(topleft=(self.x, self.y))
    def update(self):
        self.y += fall_speed
        self.rect.y = self.y
    def draw(self):
        screen.blit(self.image, (self.x, self.y))

# --- Game variables ---
arrows = []
spawn_timer = 0
hit_y = HEIGHT - 200 + (arrow_size // 2) - 10
hit_zone = pygame.Rect(0, hit_y, WIDTH, 20)
game_over = False
shake_timer = 0
pop_timers = [0,0,0,0]
bg_flash_timer = 0

# Retry/Menu buttons
button_width, button_height = 150, 60
retry_button = pygame.Rect(WIDTH//2 - button_width - 10, HEIGHT//2 + 50, button_width, button_height)
menu_button = pygame.Rect(WIDTH//2 + 10, HEIGHT//2 + 50, button_width, button_height)

# --- Main menu ---
menu_active = True
button_width, button_height = 250, 70
button_spacing = 40
total_height = 3 * button_height + 2 * button_spacing
start_y = HEIGHT//2 - total_height//2 + 100  # Increase 100 to move further down

start_button = pygame.Rect(WIDTH//2 - button_width//2, start_y, button_width, button_height)
credits_button = pygame.Rect(WIDTH//2 - button_width//2, start_y + button_height + button_spacing, button_width, button_height)
quit_button = pygame.Rect(WIDTH//2 - button_width//2, start_y + 2*(button_height + button_spacing), button_width, button_height)
button_pop = [0,0,0]

# --- Credits ---
credits_active = False
credits_animation_start = 0
credits_text_alpha = 0
credits_float_speed = 0.002
credits_float_offset = 0
credits_back_button = pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 60)
credits_back_pop = 0

# --- Difficulty selection ---
difficulty_active = False
difficulty_open_time = 0
difficulty_fade_alpha = 0
difficulty_buttons = {
    "Easy": pygame.Rect(WIDTH//2 - 125, HEIGHT//2 - 100, 250, 70),
    "Normal": pygame.Rect(WIDTH//2 - 125, HEIGHT//2, 250, 70),
    "Hard": pygame.Rect(WIDTH//2 - 125, HEIGHT//2 + 100, 250, 70),
}
difficulty_back_button = pygame.Rect(20, 20, 100, 50)
difficulty_pop = {key:0 for key in difficulty_buttons}
difficulty_back_pop = 0
selected_difficulty = None

# --- Countdown ---
countdown_active = False
countdown_start = 0
countdown_numbers = ["3","2","1","GO!!"]
countdown_index = 0
last_countdown_index = -1
pop_start_time = 0

# --- Blood effects ---
blood_particles = []
blood_timer = 0

# --- Fade function ---
def fade_surface(surface, fade_in=True, speed=15):
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill(BLACK)
    if fade_in:
        for alpha in reversed(range(0, 255, speed)):
            fade.set_alpha(alpha)
            screen.blit(surface, (0,0))
            screen.blit(fade, (0,0))
            pygame.display.update()
            pygame.time.delay(10)
    else:
        for alpha in range(0, 255, speed):
            fade.set_alpha(alpha)
            screen.blit(surface, (0,0))
            screen.blit(fade, (0,0))
            pygame.display.update()
            pygame.time.delay(10)

# Load credit images
credit_imgs = []
credit_img_files = ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg", "img5.jpg"]  # Use your actual filenames
for fname in credit_img_files:
    img = pygame.image.load(os.path.join(BASE_DIR, fname)).convert_alpha()
    img = pygame.transform.smoothscale(img, (120, 120))  # Adjust size as needed
    credit_imgs.append(img)

credit_img_positions = []
for i in range(len(credit_imgs)):
    x = random.randint(0, WIDTH - 120)
    y = random.randint(0, HEIGHT - 120)
    credit_img_positions.append((x, y))

# --- Game loop ---
running = True
while running:
    now = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(BG_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Menu ---
        if menu_active and not difficulty_active and not credits_active:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    button_pop[0] = now
                    difficulty_active = True
                    difficulty_open_time = now
                    difficulty_fade_alpha = 0
                elif credits_button.collidepoint(event.pos):
                    button_pop[1] = now
                    credits_active = True
                    credits_animation_start = pygame.time.get_ticks()
                elif quit_button.collidepoint(event.pos):
                    button_pop[2] = now
                    pygame.time.delay(100)
                    running = False

        # --- Credits ---
        if credits_active and event.type == pygame.MOUSEBUTTONDOWN:
            if credits_back_button.collidepoint(event.pos):
                credits_back_pop = now
                credits_active = False
        if credits_active:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                for idx, (img, (x, y)) in enumerate(zip(credit_imgs, credit_img_positions)):
                    float_offset = math.sin(pygame.time.get_ticks() * 0.002 + idx) * 20
                    rect = pygame.Rect(x, y + float_offset, img.get_width(), img.get_height())
                    if rect.collidepoint(mx, my):
                        dragging_idx = idx
                        drag_offset = (mx - x, my - (y + float_offset))
                        break
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging_idx = None
            elif event.type == pygame.MOUSEMOTION and dragging_idx is not None:
                mx, my = event.pos
                credit_img_positions[dragging_idx] = (mx - drag_offset[0], my - drag_offset[1])

        # --- Difficulty selection ---
        if difficulty_active and event.type == pygame.MOUSEBUTTONDOWN:
            if now - difficulty_open_time > 200:
                for key, rect in difficulty_buttons.items():
                    if rect.collidepoint(event.pos):
                        difficulty_pop[key] = now
                        selected_difficulty = key
                        if key == "Easy":
                            fall_speed = 8
                        elif key == "Normal":
                            fall_speed = 12
                        else:
                            fall_speed = 15
                        difficulty_active = False
                        menu_active = False
                        countdown_active = True
                        countdown_start = now
                        countdown_index = 0
                        last_countdown_index = -1
                        arrows.clear()
                        spawn_timer = 0
                        score = 0
                        health = 5
                        fade_surface(screen, fade_in=True)

                        # --- Stop menu music when starting the game ---  # MUSIC ADDED
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.stop()
            if difficulty_back_button.collidepoint(event.pos):
                difficulty_back_pop = now
                difficulty_active = False

        # --- Gameplay ---
        if not menu_active and not game_over and not countdown_active:
            if event.type == pygame.KEYDOWN:
                if event.key in keys:
                    i = keys.index(event.key)
                    hit = False
                    for arrow in arrows:
                        wide_rect = arrow.rect.inflate(60,0)
                        if arrow.index == i and hit_zone.colliderect(wide_rect):
                            score += 10
                            arrows.remove(arrow)
                            pop_timers[i] = now
                            hit = True
                            break
                    if not hit:
                        shake_timer = now
                        bg_flash_timer = now

        if not menu_active and game_over:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_button.collidepoint(event.pos):
                    score = 0
                    health = 5
                    arrows.clear()
                    game_over = False
                    blood_particles.clear()
                    countdown_active = True
                    countdown_start = now
                    countdown_index = 0
                    last_countdown_index = -1  # <-- Reset here!
                    spawn_timer = 0
                elif menu_button.collidepoint(event.pos):
                    score = 0
                    health = 5
                    arrows.clear()
                    game_over = False
                    blood_particles.clear()
                    menu_active = True

    # --- Draw menu ---
    if menu_active:
        screen.blit(menu_bg, (0,0))
        if credits_active:
            anim_time = pygame.time.get_ticks() - credits_animation_start
            progress = min(anim_time / 500, 1)
            credits_text_alpha = int(255 * progress)
            credits_float_offset = math.sin(anim_time * credits_float_speed) * 10

            bg_surf = pygame.Surface((WIDTH, HEIGHT))
            bg_surf.fill(BLACK)
            bg_surf.set_alpha(180)
            screen.blit(bg_surf, (0,0))

            # --- Add this block here ---
            for idx, (img, (x, y)) in enumerate(zip(credit_imgs, credit_img_positions)):
                float_offset = math.sin(pygame.time.get_ticks() * 0.002 + idx) * 20
                screen.blit(img, (x, y + float_offset))
            # --- End block ---

            title_surf = title_font.render("Credits", True, WHITE)
            title_surf.set_alpha(credits_text_alpha)
            title_rect = title_surf.get_rect(center=(WIDTH//2, HEIGHT//4 + credits_float_offset))
            screen.blit(title_surf, title_rect)

            lines = ["Pygames by Rafael", "BSIS-2A"]
            for i, line in enumerate(lines):
                text_surf = font.render(line, True, WHITE)
                text_surf.set_alpha(credits_text_alpha)
                y_pos = HEIGHT//2 - 20 + i*50 + credits_float_offset
                text_rect = text_surf.get_rect(center=(WIDTH//2, y_pos))
                screen.blit(text_surf, text_rect)

            draw_rect = credits_back_button.copy()
            if now - credits_back_pop < 150:
                scale = 1.1
                w,h = int(credits_back_button.width*scale), int(credits_back_button.height*scale)
                draw_rect.width, draw_rect.height = w,h
                draw_rect.center = credits_back_button.center
            pygame.draw.rect(screen, WHITE, draw_rect, border_radius=15)
            back_text = font.render("Back", True, BLACK)
            screen.blit(back_text, (draw_rect.centerx - back_text.get_width()//2,
                                    draw_rect.centery - back_text.get_height()//2))

        elif difficulty_active:
            # Fade-in animation
            fade_duration = 500
            progress = min((now - difficulty_open_time) / fade_duration, 1)
            difficulty_fade_alpha = int(255 * progress)

            # Semi-transparent background
            bg_surf = pygame.Surface((WIDTH, HEIGHT))
            bg_surf.fill(BLACK)
            bg_surf.set_alpha(int(150 * progress))
            screen.blit(bg_surf, (0,0))

            # Title
            title_surf = title_font.render("Select Difficulty", True, WHITE)
            title_surf.set_alpha(difficulty_fade_alpha)
            title_rect = title_surf.get_rect(center=(WIDTH//2, HEIGHT//4 - 40))
            screen.blit(title_surf, title_rect)

            # Difficulty buttons
            for key, rect in difficulty_buttons.items():
                color = (200,200,255) if rect.collidepoint(mouse_pos) else WHITE
                draw_rect = rect.copy()
                if now - difficulty_pop[key] < 150:
                    scale = 1.1
                    w,h = int(rect.width*scale), int(rect.height*scale)
                    draw_rect.width, draw_rect.height = w,h
                    draw_rect.center = rect.center
                button_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(button_surf, color, button_surf.get_rect(), border_radius=15)
                button_surf.set_alpha(difficulty_fade_alpha)
                screen.blit(button_surf, draw_rect.topleft)

                text = font.render(key, True, BLACK)
                text.set_alpha(difficulty_fade_alpha)
                text_rect = text.get_rect(center=draw_rect.center)
                screen.blit(text, text_rect)

            # Back button
            draw_rect = difficulty_back_button.copy()
            if now - difficulty_back_pop < 150:
                scale = 1.1
                w,h = int(difficulty_back_button.width*scale), int(difficulty_back_button.height*scale)
                draw_rect.width, draw_rect.height = w,h
                draw_rect.center = difficulty_back_button.center
            back_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(back_surf, WHITE, back_surf.get_rect(), border_radius=10)
            back_surf.set_alpha(difficulty_fade_alpha)
            screen.blit(back_surf, draw_rect.topleft)

            back_text = font.render("Back", True, BLACK)
            back_text.set_alpha(difficulty_fade_alpha)
            screen.blit(back_text, (draw_rect.centerx - back_text.get_width()//2,
                                    draw_rect.centery - back_text.get_height()//2))

        else:
            for idx, btn in enumerate([start_button, credits_button, quit_button]):
                color = (200,200,255) if btn.collidepoint(mouse_pos) else WHITE
                draw_rect = btn.copy()
                if now - button_pop[idx] < 150:
                    scale = 1.1
                    w,h = int(button_width*scale), int(button_height*scale)
                    draw_rect.width, draw_rect.height = w,h
                    draw_rect.center = btn.center
                pygame.draw.rect(screen, color, draw_rect, border_radius=15)
                text = "Start Game" if idx==0 else ("Credits" if idx==1 else "Quit")
                text_surf = font.render(text, True, BLACK)
                text_rect = text_surf.get_rect(center=draw_rect.center)
                screen.blit(text_surf, text_rect)

            # Draw title image with black outline
            float_offset = math.sin(pygame.time.get_ticks() * 0.002) * 18  # Floating effect for the title
            title_img = title_font.render("BUTTON SMASHER!!", True, WHITE)
            title_rect = title_img.get_rect(center=(WIDTH//2, start_y - 165 + float_offset))
            for dx in [-3, 0, 3]:
                for dy in [-3, 0, 3]:
                    if dx != 0 or dy != 0:
                        # Draw outline by blitting a black version of the image
                        black_img = title_img.copy()
                        black_img.fill((0,0,0,255), special_flags=pygame.BLEND_RGBA_MULT)
                        screen.blit(black_img, title_rect.move(dx, dy))
            # Draw main image on top
            screen.blit(title_img, title_rect)

    # --- Gameplay ---
    else:
        screen.blit(game_bg, (0, 0))
        if countdown_active:
            elapsed = (now - countdown_start) // 500  # 500ms per number (was 1000)
            if elapsed < len(countdown_numbers):
                text = countdown_numbers[elapsed]
                # Detect when the countdown number changes
                if elapsed != last_countdown_index:
                    pop_start_time = now
                    last_countdown_index = elapsed
                # Pop effect only for 150ms after number changes
                if now - pop_start_time < 150:
                    scale = 1.5
                else:
                    scale = 1.0
                surf = count_font.render(text, True, WHITE)
                surf = pygame.transform.smoothscale(surf, (int(surf.get_width()*scale), int(surf.get_height()*scale)))
                rect = surf.get_rect(center=(WIDTH//2, HEIGHT//2))
                screen.blit(surf, rect)
            else:
                countdown_active = False
                last_countdown_index = -1  # Reset for next time

        else:
            if now - bg_flash_timer < 400:
                alpha = 255 - int((now - bg_flash_timer)/400*255)
                red_overlay = pygame.Surface((WIDTH, HEIGHT))
                red_overlay.fill(RED)
                red_overlay.set_alpha(alpha)
                screen.blit(red_overlay, (0,0))

            if not game_over:
                # Set spawn interval based on difficulty
                if 'next_spawn' not in locals():
                    next_spawn = random.randint(20, 50)
                spawn_timer += 1
                if spawn_timer > next_spawn:
                    if selected_difficulty == "Easy":
                        # Only one arrow at a time, regular interval
                        lane_index = random.randint(0, 3)
                        lane = lanes[lane_index]
                        arrows.append(Arrow(lane, lane_index))
                        next_spawn = random.randint(35, 50)
                    elif selected_difficulty == "Normal":
                        # 10% chance to spawn two arrows at once (different lanes), no bursts
                        if random.random() < 0.1:
                            lanes_indices = random.sample(range(4), 2)
                            for lane_index in lanes_indices:
                                lane = lanes[lane_index]
                                arrows.append(Arrow(lane, lane_index))
                        else:
                            lane_index = random.randint(0, 3)
                            lane = lanes[lane_index]
                            arrows.append(Arrow(lane, lane_index))
                        next_spawn = random.randint(25, 45)
                    else:
                        # Hard: keep complex mechanic
                        # 20% chance to spawn two arrows at once (different lanes)
                        if random.random() < 0.2:
                            lanes_indices = random.sample(range(4), 2)
                            for lane_index in lanes_indices:
                                lane = lanes[lane_index]
                                arrows.append(Arrow(lane, lane_index))
                        # 10% chance for a burst: 3 arrows in a row (same lane)
                        elif random.random() < 0.1:
                            lane_index = random.randint(0, 3)
                            lane = lanes[lane_index]
                            for i in range(3):
                                arrows.append(Arrow(lane, lane_index))
                        else:
                            lane_index = random.randint(0, 3)
                            lane = lanes[lane_index]
                            arrows.append(Arrow(lane, lane_index))
                        next_spawn = random.randint(20, 50)
                    spawn_timer = 0

                for arrow in arrows[:]:
                    arrow.update()
                    arrow.draw()
                    if arrow.y > HEIGHT:
                        arrows.remove(arrow)
                        health -=1
                        if health <=0 and not game_over:
                            game_over = True
                            current_game_over_text = random.choice(game_over_phrases)
                            blood_timer = pygame.time.get_ticks()
                            for _ in range(20):
                                x = random.randint(0, WIDTH)
                                y = random.randint(0, HEIGHT)
                                radius = random.randint(10, 30)
                                alpha = 255
                                blood_particles.append([x, y, radius, alpha])

                if selected_difficulty and score > highscores[selected_difficulty]:
                    highscores[selected_difficulty] = score

                for i, lane in enumerate(lanes):
                    img = arrow_images[i]
                    draw_x, draw_y = lane, HEIGHT - 200
                    if now - shake_timer < 150:
                        draw_x += random.randint(-5,5)
                        draw_y += random.randint(-5,5)
                    if now - pop_timers[i] < 150:
                        scale = 1.3
                        size = int(arrow_size*scale)
                        popped = pygame.transform.smoothscale(img, (size,size))
                        rect = popped.get_rect(center=(lane+arrow_size//2, HEIGHT-200+arrow_size//2))
                        screen.blit(popped, rect.topleft)
                    else:
                        screen.blit(img, (draw_x,draw_y))

                score_text = font.render(f"Score: {score}", True, WHITE)
                if selected_difficulty:
                    highscore_text = font.render(f"Highscore ({selected_difficulty}): {highscores[selected_difficulty]}", True, WHITE)
                else:
                    highscore_text = font.render("Highscore: 0", True, WHITE)
                health_text = font.render(f"Health: {health}", True, WHITE)
                diff_text = font.render(f"Mode: {selected_difficulty}", True, (200,200,255))
                screen.blit(score_text, (20,20))
                screen.blit(highscore_text, (20,60))
                screen.blit(health_text, (20,100))
                screen.blit(diff_text, (20,140))

            if game_over:
                elapsed = pygame.time.get_ticks() - blood_timer
                fade_alpha = max(0, 255 - int(elapsed / 2))
                red_overlay = pygame.Surface((WIDTH, HEIGHT))
                red_overlay.fill(RED)
                red_overlay.set_alpha(fade_alpha)
                screen.blit(red_overlay, (0,0))

                for particle in blood_particles[:]:
                    x, y, radius, alpha = particle
                    blood_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(blood_surf, (255, 0, 0, alpha), (radius, radius), radius)
                    screen.blit(blood_surf, (x-radius, y-radius))
                    particle[3] -= 3
                    if particle[3] <= 0:
                        blood_particles.remove(particle)

                game_over_text = title_font.render("GAME OVER", True, RED)
                game_over_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2.5 - 100))
                screen.blit(game_over_text, game_over_rect)

                phrase_text = font.render(current_game_over_text, True, WHITE)
                phrase_rect = phrase_text.get_rect(center=(WIDTH//2, HEIGHT//2.1 - 40))
                screen.blit(phrase_text, phrase_rect)

                for rect, label in [(retry_button,"Retry"),(menu_button,"Menu")]:
                    pygame.draw.rect(screen, WHITE, rect, border_radius=15)
                    text = font.render(label, True, BLACK)
                    text_rect = text.get_rect(center=rect.center)
                    screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(60)

# --- Save highscores to file ---
with open(highscore_file, "w") as f:
    for diff, val in highscores.items():
        f.write(f"{diff}:{val}\n")

pygame.quit()
