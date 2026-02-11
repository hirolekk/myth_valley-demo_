#!/usr/bin/env python3
# MYTH VALLEY - DEMO W HEARTHWOOD VILLAGE
# Świat: Ashen Vale
# Pełna wersja z grafiką, NPC, dialogami, ekwipunkiem

import pygame
import sys
import random
import math

# ============================================
# INICJALIZACJA
# ============================================

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("MYTH VALLEY - Demo w Hearthwood")
clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 48)
font_medium = pygame.font.Font(None, 32)
font_small = pygame.font.Font(None, 24)

# Kolory
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (80, 80, 80)
COLOR_DARK_GRAY = (40, 40, 40)
COLOR_ASH = (120, 120, 120)
COLOR_ASH_LIGHT = (180, 180, 180)
COLOR_GREEN_DARK = (20, 50, 20)
COLOR_GREEN = (40, 80, 40)
COLOR_BROWN = (80, 50, 20)
COLOR_BROWN_LIGHT = (120, 80, 40)
COLOR_WOOD = (100, 60, 30)
COLOR_STONE = (70, 70, 70)
COLOR_WATER = (100, 150, 150)
COLOR_GOLD = (200, 170, 0)
COLOR_RED = (150, 30, 30)
COLOR_BLUE = (50, 100, 200)
COLOR_PURPLE = (120, 50, 150)

# ============================================
# SYSTEM EKWIPUNKU
# ============================================

class Item:
    def __init__(self, id, name, description, icon_char="■"):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon_char
        
class Inventory:
    def __init__(self):
        self.items = []
        self.max_slots = 8
        
    def add(self, item):
        if len(self.items) < self.max_slots:
            self.items.append(item)
            return True
        return False
        
    def remove(self, item_id):
        for i, item in enumerate(self.items):
            if item.id == item_id:
                return self.items.pop(i)
        return None
        
    def has(self, item_id):
        return any(item.id == item_id for item in self.items)

# ============================================
# SYSTEM RELACJI
# ============================================

class Reputation:
    def __init__(self):
        self.values = {
            "arin": 0,
            "lyra": 0,
            "borin": 0,
            "kael": 0,
            "debugger": 0,
            "elin": 0,
            "maev": 0
        }
        
    def modify(self, npc_id, amount):
        if npc_id in self.values:
            self.values[npc_id] += amount
            self.values[npc_id] = max(-100, min(100, self.values[npc_id]))
            return True
        return False
        
    def get(self, npc_id):
        return self.values.get(npc_id, 0)

# ============================================
# GŁÓWNY STAN GRY
# ============================================

class GameState:
    def __init__(self):
        self.scene = "opening"
        self.inventory = Inventory()
        self.reputation = Reputation()
        self.decisions = []
        self.has_met_debugger = False
        self.sanctuary_choice = None
        self.quest_borin_complete = False
        self.quest_lyra_complete = False
        self.play_time = 0
        self.message = ""
        self.message_timer = 0
        
        # Startowe przedmioty
        self.inventory.add(Item("medalion", "Stary Medalion", "Ktoś go zgubił w Ashen Vale. Ktoś inny znajdzie.", "◎"))
        
    def show_message(self, text, duration=3.0):
        self.message = text
        self.message_timer = duration
        
    def update(self, dt):
        self.play_time += dt
        if self.message_timer > 0:
            self.message_timer -= dt

# ============================================
# SYSTEM DIALOGÓW
# ============================================

class DialogueNode:
    def __init__(self, text):
        self.text = text
        self.choices = []
        
class DialogueChoice:
    def __init__(self, text, next_node=None, reputation_effect=None, item_gain=None, decision=None):
        self.text = text
        self.next_node = next_node
        self.reputation_effect = reputation_effect
        self.item_gain = item_gain
        self.decision = decision

class DialogueSystem:
    def __init__(self, game_state):
        self.game = game_state
        self.active = False
        self.current_npc = None
        self.current_node = None
        self.nodes = {}
        
    def start(self, npc_id):
        self.active = True
        self.current_npc = npc_id
        self.load_dialogue(npc_id)
        
    def load_dialogue(self, npc_id):
        self.nodes = {}
        
        if npc_id == "kael":
            n1 = DialogueNode("Stój. Nie znam cię. Arin cię oczekuje. Idź prosto do Dębu.")
            n1.choices = [
                DialogueChoice("Dziękuję. Idę.", "end", ("kael", 5)),
                DialogueChoice("Kim jest Debugger?", "debugger_info", ("kael", -2)),
            ]
            if self.game.reputation.get("kael") < 0:
                n1.choices.append(DialogueChoice("...odsuń się.", "confront", ("kael", -10)))
            self.nodes["start"] = n1
            
            n2 = DialogueNode("Debugger? On... jest. Czasem go nie ma. Czasem jest dwóch. Nie pytaj. Lepiej nie wiedzieć.")
            n2.choices = [DialogueChoice("...", "end")]
            self.nodes["debugger_info"] = n2
            
            n3 = DialogueNode("Mam rozkaz. Nie wejdziesz siłą.")
            n3.choices = [DialogueChoice("Przepraszam.", "end", ("kael", 5))]
            self.nodes["confront"] = n3
            
        elif npc_id == "arin":
            n1 = DialogueNode("Witaj w Hearthwood. Widzę ten symbol na twojej ręce. Potrzebuję twojej pomocy. Pomóż moim ludziom, a pokażę ci Sanktuarium.")
            n1.choices = [
                DialogueChoice("Pomogę.", "end", ("arin", 10)),
                DialogueChoice("Kim jesteś?", "arin_info", ("arin", 0)),
                DialogueChoice("Co to za symbol?", "symbol_info", ("arin", 5))
            ]
            self.nodes["start"] = n1
            
            n2 = DialogueNode("Jestem Starszym tej wioski. Prowadzę ją od... dawna. Zanim przyszedł popiół. Zanim odeszli.")
            n2.choices = [DialogueChoice("...", "start")]
            self.nodes["arin_info"] = n2
            
            n3 = DialogueNode("To znak Myth Bound. Mocy która przenika Ashen Vale. Miał go mój syn. Miała go moja żona. Oboje odeszli do lasu.")
            n3.choices = [DialogueChoice("Przykro mi.", "start", ("arin", 10))]
            self.nodes["symbol_info"] = n3
            
        elif npc_id == "debugger":
            if not self.game.has_met_debugger:
                n1 = DialogueNode("*klika w powietrze* ...interesujące. Nowy gracz. Nowa instancja. Witaj w Ashen Vale. Albo jak ja to nazywam: build 0.7.3.")
                n1.choices = [
                    DialogueChoice("Kim jesteś?", "who", ("debugger", 5)),
                    DialogueChoice("Co robisz?", "what", ("debugger", 0)),
                    DialogueChoice("...odchodzę.", "end", ("debugger", -5))
                ]
                self.nodes["start"] = n1
                
                n2 = DialogueNode("Debugger. Naprawiacz. Glitch. Mam wiele nazw. Prawdziwe imię? Nie pamiętam. Bug w matrixie. Albo matrix we mnie.")
                n2.choices = [DialogueChoice("...", "start")]
                self.nodes["who"] = n2
                
                n3 = DialogueNode("Naprawiam rzeczywistość. Albo to co z niej zostało. Widzisz te pęknięcia? Ktoś musi to robić.")
                n3.choices = [DialogueChoice("Dziękuję?", "start", ("debugger", 10))]
                self.nodes["what"] = n3
                
                self.game.has_met_debugger = True
            else:
                n1 = DialogueNode("Znowu ty. Uważaj na Sanktuarium. To miejsce... testuje. Sprawdza czy jesteś gotowy. Na co? Nie wiem. Nikt nie wie.")
                n1.choices = [
                    DialogueChoice("Idę tam.", "end"),
                    DialogueChoice("Boisz się?", "fear", ("debugger", -10))
                ]
                self.nodes["start"] = n1
                
                n2 = DialogueNode("Boję? Nie. Obawiam się? Może. Kiedy spędzisz tyle czasu w jednym buildzie, zaczynasz rozumieć, że niektóre bugi... to nie bugi. To funkcje.")
                n2.choices = [DialogueChoice("...", "start")]
                self.nodes["fear"] = n2
        
        end = DialogueNode("...")
        end.choices = [DialogueChoice("[Koniec rozmowy]", None)]
        self.nodes["end"] = end
        
        self.current_node = self.nodes.get("start", end)
        
    def select_choice(self, index):
        if not self.current_node or index >= len(self.current_node.choices):
            self.active = False
            return
            
        choice = self.current_node.choices[index]
        
        if choice.reputation_effect:
            npc, amount = choice.reputation_effect
            self.game.reputation.modify(npc, amount)
            
        if choice.item_gain:
            self.game.inventory.add(choice.item_gain)
            self.game.show_message(f"Otrzymałeś: {choice.item_gain.name}", 2)
            
        if choice.decision:
            self.game.decisions.append(choice.decision)
            
        if choice.next_node and choice.next_node in self.nodes:
            self.current_node = self.nodes[choice.next_node]
        elif choice.next_node is None:
            self.active = False
        else:
            self.current_node = self.nodes.get("end", self.nodes.get("start"))
            
    def draw(self, screen):
        if not self.active or not self.current_node:
            return
            
        s = pygame.Surface((SCREEN_WIDTH - 200, 200))
        s.set_alpha(220)
        s.fill(COLOR_BLACK)
        screen.blit(s, (100, SCREEN_HEIGHT - 250))
        
        pygame.draw.rect(screen, COLOR_ASH, (100, SCREEN_HEIGHT - 250, SCREEN_WIDTH - 200, 200), 2)
        
        name_text = font_medium.render(f"{self.current_npc.upper()}", True, COLOR_ASH_LIGHT)
        screen.blit(name_text, (120, SCREEN_HEIGHT - 240))
        
        y_offset = SCREEN_HEIGHT - 200
        words = self.current_node.text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font_small.size(test_line)[0] < SCREEN_WIDTH - 250:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
            
        for i, line in enumerate(lines[:4]):
            text = font_small.render(line, True, COLOR_WHITE)
            screen.blit(text, (120, y_offset + i * 30))
            
        for i, choice in enumerate(self.current_node.choices[:4]):
            y = SCREEN_HEIGHT - 80 + i * 30
            text = font_small.render(f"{i+1}. {choice.text}", True, COLOR_GOLD)
            screen.blit(text, (120, y))

# ============================================
# HEARTHWOOD VILLAGE - GRAFIKA
# ============================================

class HearthwoodVillage:
    def __init__(self):
        self.buildings = [
            {"name": "WIĘCISTY DĄB", "x": 500, "y": 300, "w": 80, "h": 120, "color": COLOR_BROWN, "type": "tree"},
            {"name": "KUŹNIA", "x": 300, "y": 250, "w": 60, "h": 50, "color": COLOR_STONE, "type": "forge"},
            {"name": "CHATA LYRY", "x": 150, "y": 350, "w": 50, "h": 40, "color": COLOR_WOOD, "type": "house"},
            {"name": "DOM ARINA", "x": 650, "y": 280, "w": 55, "h": 45, "color": COLOR_WOOD, "type": "house"},
            {"name": "GOSPODA", "x": 750, "y": 350, "w": 70, "h": 55, "color": COLOR_BROWN_LIGHT, "type": "inn"},
            {"name": "OPUSZCZONA CHATA", "x": 900, "y": 400, "w": 45, "h": 35, "color": COLOR_DARK_GRAY, "type": "ruin"}
        ]
        
        self.npc_positions = {
            "kael": (200, 200),
            "arin": (520, 280),
            "lyra": (160, 330),
            "borin": (310, 230),
            "debugger": (random.randint(100, 1000), random.randint(150, 500)),
            "elin": (550, 380),
            "maev": (480, 320)
        }
        
        self.trees = [(x, y) for x in range(50, 1200, 80) for y in range(50, 600, 100)]
        self.trees = random.sample(self.trees, 30)
        
        self.ash_particles = []
        for _ in range(100):
            self.ash_particles.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "speed": random.uniform(1, 3)
            })
            
    def update(self):
        for p in self.ash_particles:
            p["y"] += p["speed"]
            if p["y"] > SCREEN_HEIGHT:
                p["y"] = 0
                p["x"] = random.randint(0, SCREEN_WIDTH)
                
        if "debugger" in self.npc_positions:
            x, y = self.npc_positions["debugger"]
            x += random.randint(-10, 10)
            y += random.randint(-5, 5)
            x = max(50, min(1200, x))
            y = max(50, min(600, y))
            self.npc_positions["debugger"] = (x, y)
            
    def draw(self, screen):
        for i in range(SCREEN_HEIGHT):
            color_val = int(40 + i * 0.1)
            color = (color_val, color_val, color_val + 10)
            pygame.draw.line(screen, color, (0, i), (SCREEN_WIDTH, i))
            
        pygame.draw.polygon(screen, COLOR_DARK_GRAY, [(0, 400), (200, 200), (400, 400)])
        pygame.draw.polygon(screen, COLOR_DARK_GRAY, [(300, 450), (600, 150), (900, 450)])
        pygame.draw.polygon(screen, COLOR_DARK_GRAY, [(700, 400), (1000, 250), (1200, 400)])
        
        for x, y in self.trees:
            pygame.draw.rect(screen, COLOR_BROWN, (x, y, 10, 40))
            pygame.draw.circle(screen, COLOR_GREEN_DARK, (x + 5, y - 15), 20)
            
        river_points = [(0, 550), (200, 520), (400, 530), (600, 540), (800, 520), (1000, 550), (1280, 530)]
        for i in range(len(river_points) - 1):
            pygame.draw.line(screen, COLOR_WATER, river_points[i], river_points[i + 1], 30)
            pygame.draw.line(screen, (80, 120, 120), river_points[i], river_points[i + 1], 28)
            
        for b in self.buildings:
            x, y, w, h = b["x"], b["y"], b["w"], b["h"]
            
            if b["type"] == "tree":
                pygame.draw.rect(screen, COLOR_BROWN, (x + 20, y + 60, 10, 60))
                pygame.draw.circle(screen, COLOR_GREEN, (x + 25, y + 50), 40)
                pygame.draw.circle(screen, COLOR_GREEN_DARK, (x + 25, y + 50), 30)
                pygame.draw.circle(screen, COLOR_BLUE, (x - 10, y + 20), 5)
                pygame.draw.circle(screen, COLOR_BLUE, (x + 60, y + 40), 5)
                
            elif b["type"] == "forge":
                pygame.draw.rect(screen, COLOR_STONE, (x, y, w, h))
                pygame.draw.rect(screen, COLOR_RED, (x + 20, y - 10, 20, 10))
                for i in range(5):
                    pygame.draw.circle(screen, (200, 100, 0), (x + 30, y - 15 + i * 2), 3)
                    
            elif b["type"] == "house":
                pygame.draw.rect(screen, b["color"], (x, y, w, h))
                pygame.draw.polygon(screen, COLOR_BROWN, [(x - 5, y), (x + w//2, y - 15), (x + w + 5, y)])
                pygame.draw.rect(screen, COLOR_GOLD, (x + 10, y + 10, 8, 8))
                pygame.draw.rect(screen, COLOR_GOLD, (x + 30, y + 10, 8, 8))
                pygame.draw.rect(screen, COLOR_BROWN, (x + 20, y + 25, 10, 15))
                
            elif b["type"] == "inn":
                pygame.draw.rect(screen, b["color"], (x, y, w, h))
                pygame.draw.polygon(screen, COLOR_BROWN, [(x - 5, y), (x + w//2, y - 20), (x + w + 5, y)])
                pygame.draw.circle(screen, COLOR_WOOD, (x + w//2, y - 30), 12)
                pygame.draw.circle(screen, COLOR_ASH, (x + w//2, y - 30), 8)
                
            elif b["type"] == "ruin":
                pygame.draw.rect(screen, COLOR_DARK_GRAY, (x, y, w, h))
                pygame.draw.line(screen, COLOR_BLACK, (x, y), (x + w, y + h), 3)
                pygame.draw.line(screen, COLOR_BLACK, (x + w, y), (x, y + h), 3)
                
        for npc_id, (x, y) in self.npc_positions.items():
            if npc_id == "kael":
                color = COLOR_BLUE
                char = "⚔"
            elif npc_id == "arin":
                color = COLOR_GOLD
                char = "👑"
            elif npc_id == "lyra":
                color = COLOR_GREEN
                char = "🌿"
            elif npc_id == "borin":
                color = COLOR_STONE
                char = "🔨"
            elif npc_id == "debugger":
                color = COLOR_PURPLE
                char = "⚡"
            elif npc_id == "elin":
                color = COLOR_WHITE
                char = "★"
            elif npc_id == "maev":
                color = COLOR_GRAY
                char = "◈"
            else:
                color = COLOR_WHITE
                char = "●"
                
            pygame.draw.circle(screen, color, (x, y), 10)
            text = font_small.render(char, True, COLOR_WHITE)
            screen.blit(text, (x - 8, y - 20))
            name_text = font_small.render(npc_id.upper(), True, COLOR_ASH_LIGHT)
            screen.blit(name_text, (x - 20, y - 40))
            
        for p in self.ash_particles:
            alpha = random.randint(100, 200)
            pygame.draw.circle(screen, (alpha, alpha, alpha), (int(p["x"]), int(p["y"])), 1)

# ============================================
# GŁÓWNA PĘTLA GRY
# ============================================

def main():
    game = GameState()
    dialogue = DialogueSystem(game)
    village = HearthwoodVillage()
    
    player_x = 100
    player_y = 500
    
    opening_timer = 0
    running = True
    
    while running:
        dt = clock.tick(60) / 1000.0
        game.update(dt)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    
                if dialogue.active:
                    if event.key == pygame.K_1:
                        dialogue.select_choice(0)
                    elif event.key == pygame.K_2:
                        dialogue.select_choice(1)
                    elif event.key == pygame.K_3:
                        dialogue.select_choice(2)
                    elif event.key == pygame.K_4:
                        dialogue.select_choice(3)
        
        if game.scene == "opening":
            opening_timer += dt
            if opening_timer > 5:
                game.scene = "hearthwood"
                
        elif not dialogue.active and game.scene != "opening":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= 5
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += 5
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                player_y -= 5
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                player_y += 5
                
            player_x = max(50, min(SCREEN_WIDTH - 50, player_x))
            player_y = max(50, min(SCREEN_HEIGHT - 50, player_y))
            
            if keys[pygame.K_e]:
                for npc_id, (nx, ny) in village.npc_positions.items():
                    dist = math.sqrt((player_x - nx)**2 + (player_y - ny)**2)
                    if dist < 50:
                        dialogue.start(npc_id)
                        pygame.time.wait(300)
                        break
        
        village.update()
        screen.fill(COLOR_BLACK)
        
        if game.scene == "opening":
            if opening_timer < 1:
                text = font_large.render("MYTH VALLEY", True, COLOR_ASH_LIGHT)
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - 50))
                text = font_medium.render("DEMO", True, COLOR_ASH)
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 + 20))
            elif opening_timer < 2:
                text = font_medium.render("Zamknij oczy...", True, COLOR_WHITE)
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
            elif opening_timer < 3:
                text = font_medium.render("Oddychaj...", True, COLOR_WHITE)
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
            elif opening_timer < 4:
                text = font_medium.render("Zapomnij, co wiesz...", True, COLOR_WHITE)
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
            elif opening_timer < 5:
                text = font_medium.render("Teraz otwórz.", True, COLOR_WHITE)
                screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
        else:
            village.draw(screen)
            
            pygame.draw.circle(screen, COLOR_WHITE, (player_x, player_y), 12)
            pygame.draw.circle(screen, COLOR_GOLD, (player_x, player_y), 8)
            pygame.draw.circle(screen, COLOR_PURPLE, (player_x + 10, player_y - 5), 3)
            
            inv_x = 20
            inv_y = 20
            for i, item in enumerate(game.inventory.items[:8]):
                pygame.draw.rect(screen, COLOR_DARK_GRAY, (inv_x + i * 45, inv_y, 40, 40), 1)
                if i < len(game.inventory.items):
                    text = font_medium.render(item.icon, True, COLOR_GOLD)
                    screen.blit(text, (inv_x + i * 45 + 12, inv_y + 8))
                    if i == 0:
                        name_text = font_small.render(item.name, True, COLOR_ASH_LIGHT)
                        screen.blit(name_text, (inv_x + i * 45, inv_y + 45))
                        
            rep_y = 80
            for i, (npc, val) in enumerate(game.reputation.values.items()):
                if i < 5:
                    color = COLOR_GREEN if val > 0 else COLOR_RED if val < 0 else COLOR_WHITE
                    text = font_small.render(f"{npc}: {val}", True, color)
                    screen.blit(text, (20, rep_y + i * 20))
                    
            for npc_id, (nx, ny) in village.npc_positions.items():
                dist = math.sqrt((player_x - nx)**2 + (player_y - ny)**2)
                if dist < 50:
                    text = font_small.render(f"[E] Rozmawiaj z {npc_id}", True, COLOR_GOLD)
                    screen.blit(text, (player_x - 60, player_y - 60))
                    break
                    
        dialogue.draw(screen)
        
        fps_text = font_small.render(f"FPS: {int(clock.get_fps())}", True, COLOR_GRAY)
        screen.blit(fps_text, (SCREEN_WIDTH - 100, 20))
        
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
