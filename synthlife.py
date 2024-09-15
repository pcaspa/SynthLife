import pygame
import random
import math
from collections import Counter
import copy
import csv
import json
import os

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1800, 960
HEADER_HEIGHT = 100  # Height reserved for header at the top

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Synthetic Life Simulation")

# Fonts for labels
FONT = pygame.font.SysFont(None, 24)
LARGE_FONT = pygame.font.SysFont(None, 48)

# Clock for controlling the frame rate
clock = pygame.time.Clock()

# Colors and their corresponding attributes
ATTRIBUTE_COLORS = {
    'attack_power': (255, 0, 0),         # Red
    'defense': (0, 0, 255),              # Blue
    'speed': (0, 255, 0),                # Green
    'energy_storage': (255, 255, 0),     # Yellow
    'vision_range': (128, 0, 128),       # Purple
    'reproduction_rate': (0, 255, 255),  # Cyan
    'metabolism_rate': (255, 165, 0),    # Orange
    'stealth': (128, 128, 128),          # Gray
    'intelligence': (255, 255, 255)      # White
}

# Reverse mapping for quick color to attribute conversion
COLOR_TO_ATTRIBUTE = {v: k for k, v in ATTRIBUTE_COLORS.items()}

# Background color
BACKGROUND_COLOR = (30, 30, 30)

# Simulation parameters
NUM_PLANTS = 200
MAX_PLANTS = 200
NUM_EACH_LIFE_FORM = 10
PLANT_RESPAWN_TIME = 250

# Grouping Behavior Parameters
GROUPING_RADIUS = 100
COHESION_WEIGHT = 0.05

# Define life_types globally
life_types = ['A', 'B', 'C', 'D']

# Predefine quarters globally for enforce_boundaries method
quarters = {
    'A': ((0, HEADER_HEIGHT), (WIDTH // 2, HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2)),  # Top Left
    'B': ((WIDTH // 2, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2)),  # Top Right
    'C': ((0, HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2), (WIDTH // 2, HEIGHT)),  # Bottom Left
    'D': ((WIDTH // 2, HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2), (WIDTH, HEIGHT))   # Bottom Right
}

# Initialize gap variables
vertical_gap_start_y = 0
vertical_gap_end_y = 0
horizontal_gap_start_x = 0
horizontal_gap_end_x = 0

# Define maximum number of lifeforms per type
MAX_LIFEFORMS_PER_TYPE = 50

# Define a counter for the number of games played
games_played = -1

# Mutation rate for offspring
#MUTATION_RATE = 0.1

# Define maximum energy for LifeForms
MAX_ENERGY = 500  # *** Added: Maximum energy cap ***

# Initialize last winner variables
last_winner_type = None
consecutive_wins = 0
last_winning_parameters = None

# Define Plant class
class Plant(pygame.sprite.Sprite):
    def __init__(self, position=None):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill((34, 139, 34))  # Plant color
        self.rect = self.image.get_rect()
        if position:
            self.rect.center = position
        else:
            self.rect.center = (random.randint(0, WIDTH), random.randint(HEADER_HEIGHT, HEIGHT))
        self.energy = 25  # Energy provided when consumed

# Define LifeForm class
class LifeForm(pygame.sprite.Sprite):
    def __init__(self, life_type, position=None, pixels=None):
        super().__init__()
        self.life_type = life_type
        self.energy = 200
        self.alive = True
        if position:
            self.position = position
        else:
            self.position = [float(random.randint(0, WIDTH)), float(random.randint(HEADER_HEIGHT, HEIGHT))]
        self.pixels = pixels if pixels else self.get_initial_pixels(life_type)
        self.attributes = {}
        self.update_attributes()
        self.image = None
        self.image_cached = False
        self.create_image()
        self.rect = self.image.get_rect()
        self.rect.center = (int(self.position[0]), int(self.position[1]))
        self.target = None
        self.direction = random.uniform(0, 2 * math.pi)
        self.reproduction_cooldown = 0

    def get_initial_pixels(self, life_type):
        # Define symmetrical patterns for each life type
        if life_type == 'A':
            pixels = [
                (0, -1, ATTRIBUTE_COLORS['speed']),
                (-1, 0, ATTRIBUTE_COLORS['vision_range']),
                (0, 0, ATTRIBUTE_COLORS['speed']),
                (1, 0, ATTRIBUTE_COLORS['vision_range']),
                (0, 1, ATTRIBUTE_COLORS['speed']),
                (-1, -1, ATTRIBUTE_COLORS['speed']),
                (1, -1, ATTRIBUTE_COLORS['speed']),
                (-1, 1, ATTRIBUTE_COLORS['speed']),
                (1, 1, ATTRIBUTE_COLORS['speed']),
                (0, -2, ATTRIBUTE_COLORS['intelligence']),
            ]
        elif life_type == 'B':
            pixels = [
                (0, -1, ATTRIBUTE_COLORS['attack_power']),
                (-1, 0, ATTRIBUTE_COLORS['defense']),
                (0, 0, ATTRIBUTE_COLORS['attack_power']),
                (1, 0, ATTRIBUTE_COLORS['defense']),
                (0, 1, ATTRIBUTE_COLORS['attack_power']),
                (-1, -1, ATTRIBUTE_COLORS['defense']),
                (1, -1, ATTRIBUTE_COLORS['defense']),
                (-1, 1, ATTRIBUTE_COLORS['defense']),
                (1, 1, ATTRIBUTE_COLORS['defense']),
                (0, -2, ATTRIBUTE_COLORS['intelligence']),
            ]
        elif life_type == 'C':
            pixels = [
                (0, -1, ATTRIBUTE_COLORS['speed']),
                (-1, 0, ATTRIBUTE_COLORS['attack_power']),
                (0, 0, ATTRIBUTE_COLORS['defense']),
                (1, 0, ATTRIBUTE_COLORS['vision_range']),
                (0, 1, ATTRIBUTE_COLORS['energy_storage']),
                (-1, -1, ATTRIBUTE_COLORS['metabolism_rate']),
                (1, -1, ATTRIBUTE_COLORS['reproduction_rate']),
                (-1, 1, ATTRIBUTE_COLORS['stealth']),
                (1, 1, ATTRIBUTE_COLORS['intelligence']),
                (0, -2, ATTRIBUTE_COLORS['intelligence']),
            ]
        elif life_type == 'D':
            pixels = [
                (0, -1, ATTRIBUTE_COLORS['energy_storage']),
                (-1, 0, ATTRIBUTE_COLORS['reproduction_rate']),
                (0, 0, ATTRIBUTE_COLORS['energy_storage']),
                (1, 0, ATTRIBUTE_COLORS['reproduction_rate']),
                (0, 1, ATTRIBUTE_COLORS['energy_storage']),
                (-1, -1, ATTRIBUTE_COLORS['energy_storage']),
                (1, -1, ATTRIBUTE_COLORS['energy_storage']),
                (-1, 1, ATTRIBUTE_COLORS['energy_storage']),
                (1, 1, ATTRIBUTE_COLORS['energy_storage']),
                (0, -2, ATTRIBUTE_COLORS['intelligence']),
            ]
        else:
            pixels = self.generate_random_pixels()
        return pixels

    def generate_random_pixels(self):
        # Generate random symmetrical pixels
        pixels = []
        positions = set()
        num_pixels = 16  # Total number of pixels in the life form

        # Attribute pixel counters to enforce the maximum of 5 pixels per attribute
        attribute_pixel_counts = {attr: 0 for attr in ATTRIBUTE_COLORS.keys()}
        max_pixels_per_attribute = 5

        while len(pixels) < num_pixels:
            x = random.randint(-2, 2)
            y = random.randint(-2, 2)

            if (x, y) not in positions:
                # Select a random attribute color with the constraint of max 5 pixels per attribute
                available_colors = [
                    color for attr, color in ATTRIBUTE_COLORS.items()
                    if attribute_pixel_counts[attr] < max_pixels_per_attribute
                ]
                if not available_colors:
                    break  # This should never happen but ensures safety

                color = random.choice(available_colors)
                attribute = COLOR_TO_ATTRIBUTE[color]
                pixels.append((x, y, color))
                positions.add((x, y))
                attribute_pixel_counts[attribute] += 1

                # Add symmetrical counterpart if within bounds and within the 5x5 grid
                if x != 0 or y != 0:
                    sym_x, sym_y = -x, y
                    if (
                        (sym_x, sym_y) not in positions
                        and len(pixels) < num_pixels
                        and -2 <= sym_x <= 2
                        and -2 <= sym_y <= 2
                    ):
                        pixels.append((sym_x, sym_y, color))
                        positions.add((sym_x, sym_y))
                        attribute_pixel_counts[attribute] += 1

        # Ensure we have exactly num_pixels pixels
        if len(pixels) > num_pixels:
            pixels = pixels[:num_pixels]

        return pixels

    def update_attributes(self):
        # Count the number of pixels of each color
        color_counts = Counter([tuple(color) for _, _, color in self.pixels])
        # Initialize attributes
        self.attributes = dict.fromkeys(ATTRIBUTE_COLORS.keys(), 0)
        # Update attributes based on pixel counts
        for color, count in color_counts.items():
            attribute = COLOR_TO_ATTRIBUTE[color]
            self.attributes[attribute] = count

    def create_image(self):
        if self.image_cached:
            return
        # Create an image large enough to hold all pixels
        pixel_size = 5
        positions = [(x, y) for x, y in [(px, py) for px, py, _ in self.pixels]]
        min_x = min(x for x, y in positions)
        max_x = max(x for x, y in positions)
        min_y = min(y for x, y in positions)
        max_y = max(y for x, y in positions)
        width = (max_x - min_x + 1) * pixel_size
        height = (max_y - min_y + 1) * pixel_size
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        # Draw pixels
        for x, y, color in self.pixels:
            rect = pygame.Rect(
                (x - min_x) * pixel_size,
                (y - min_y) * pixel_size,
                pixel_size,
                pixel_size
            )
            self.image.fill(color, rect)
        # Update position offset
        self.offset = [min_x * pixel_size, min_y * pixel_size]
        self.image_cached = True

    def update(self, plants, life_forms):
        if not self.alive:
            return

        # Energy depletion over time
        metabolism = round((5 - self.attributes.get('metabolism_rate', 0)) / 2.5)
        self.energy -= 0.05 * metabolism

        # If energy runs out, die
        if self.energy <= 0:
            self.die()
            return

        # Reproduction cooldown logic
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1

        # Reproduce if energy is sufficient and cooldown has passed
        reproduction_threshold = 200 + (self.attributes['energy_storage'] * 10)
        reproduction_rate = self.attributes['reproduction_rate'] or 1

        # Check current number of lifeforms of this type
        current_count = sum(1 for lf in life_forms if lf.life_type == self.life_type and lf.alive)
        if self.energy >= reproduction_threshold and self.reproduction_cooldown == 0 and current_count < MAX_LIFEFORMS_PER_TYPE:
            # Check for another same-type life form in contact
            same_type_neighbors = pygame.sprite.spritecollide(self, life_forms, False, pygame.sprite.collide_rect)
            same_type_neighbors = [lf for lf in same_type_neighbors if lf.life_type == self.life_type and lf != self and lf.alive]

            if same_type_neighbors:
                # Choose one neighbor to reproduce with
                partner = random.choice(same_type_neighbors)
                # Check if partner can reproduce (cooldown)
                if partner.reproduction_cooldown == 0:
                    # Ensure reproduction does not exceed MAX_LIFEFORMS_PER_TYPE
                    offspring_allowed = MAX_LIFEFORMS_PER_TYPE - current_count
                    if offspring_allowed >= 2:
                        # Each parent contributes energy for one offspring
                        energy_contribution = min(self.energy, partner.energy) / 3
                        self.energy -= energy_contribution
                        partner.energy -= energy_contribution

                        # Create two offspring
                        offspring1 = self.reproduce(energy_contribution)
                        offspring2 = partner.reproduce(energy_contribution)
                        life_forms.add(offspring1, offspring2)

                        # Set cooldowns
                        self.reproduction_cooldown = 300
                        partner.reproduction_cooldown = 300
                    elif offspring_allowed == 1:
                        # Each parent contributes energy for one offspring
                        energy_contribution = min(self.energy, partner.energy) / 4
                        self.energy -= energy_contribution
                        partner.energy -= energy_contribution

                        # Create one offspring
                        offspring = self.reproduce(energy_contribution)
                        life_forms.add(offspring)

                        # Set cooldowns
                        self.reproduction_cooldown = 300
                        partner.reproduction_cooldown = 300

        # Find target if none
        if not self.target or not self.target.alive:
            self.find_target(plants, life_forms)

        # Move towards target or wander, with grouping behavior
        if self.target:
            self.move_towards_target(life_forms)
        else:
            self.wander()

        # Enforce boundaries
        self.enforce_boundaries()

        # Update rect position
        self.rect.center = (int(self.position[0]), int(self.position[1]))

    def enforce_boundaries(self):
        """
        Prevent the life form from moving outside its designated quarter.
        Adjust the direction when hitting a boundary.
        """
        global vertical_gap_start_y, vertical_gap_end_y, horizontal_gap_start_x, horizontal_gap_end_x

        # Determine which quarter the life form is in
        quarter = determine_quarter(self.position)
        if not quarter:
            return

        quarter_start, quarter_end = quarters[quarter]

        # Get image dimensions
        image_width, image_height = self.image.get_size()
        half_width = image_width / 2
        half_height = image_height / 2

        boundary_hit = False

        # Check boundaries and adjust position and direction
        if self.position[1] - half_height < HEADER_HEIGHT:
            self.position[1] = HEADER_HEIGHT + half_height
            boundary_hit = True

        if self.position[0] - half_width < 0:
            self.position[0] = half_width
            boundary_hit = True
        elif self.position[0] + half_width > WIDTH:
            self.position[0] = WIDTH - half_width
            boundary_hit = True

        if self.position[1] + half_height > HEIGHT:
            self.position[1] = HEIGHT - half_height
            boundary_hit = True

        # Vertical boundary
        if quarter in ['A', 'C']:
            if self.position[0] + half_width > WIDTH // 2:
                if not (vertical_gap_start_y <= self.position[1] <= vertical_gap_end_y):
                    self.position[0] = WIDTH // 2 - half_width
                    boundary_hit = True
        elif quarter in ['B', 'D']:
            if self.position[0] - half_width < WIDTH // 2:
                if not (vertical_gap_start_y <= self.position[1] <= vertical_gap_end_y):
                    self.position[0] = WIDTH // 2 + half_width
                    boundary_hit = True

        # Horizontal boundary
        if quarter in ['A', 'B']:
            if self.position[1] + half_height > HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2:
                if not (horizontal_gap_start_x <= self.position[0] <= horizontal_gap_end_x):
                    self.position[1] = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2 - half_height
                    boundary_hit = True
        elif quarter in ['C', 'D']:
            if self.position[1] - half_height < HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2:
                if not (horizontal_gap_start_x <= self.position[0] <= horizontal_gap_end_x):
                    self.position[1] = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2 + half_height
                    boundary_hit = True

        # Adjust direction if boundary was hit
        if boundary_hit:
            self.direction = (self.direction + math.pi) % (2 * math.pi)

    def find_target(self, plants, life_forms):
        vision_range = 100 + (self.attributes['vision_range'] * 10)
        # Potential targets within vision range
        possible_targets = []

        current_quarter = determine_quarter(self.position)

        # Detect plants within vision range and same quarter
        for plant in plants:
            if self.distance_to(plant.rect.center) <= vision_range:
                plant_quarter = determine_quarter(plant.rect.center)
                if plant_quarter == current_quarter:
                    possible_targets.append(plant)

        # Detect other life forms within vision range and same quarter
        for life_form in life_forms:
            if life_form != self and life_form.alive:
                if life_form.life_type == self.life_type:
                    continue
                distance = self.distance_to(life_form.rect.center)
                if distance <= vision_range:
                    life_form_quarter = determine_quarter(life_form.rect.center)
                    if life_form_quarter == current_quarter:
                        # Stealth and intelligence affect detection
                        detection_chance = 1 - (life_form.attributes['stealth'] * 0.05)
                        detection_chance += self.attributes['intelligence'] * 0.05
                        detection_chance = max(0, min(detection_chance, 1))
                        if random.random() < detection_chance:
                            possible_targets.append(life_form)

        if possible_targets:
            # Prioritize based on intelligence
            if self.attributes['intelligence'] > 0:
                self.target = min(possible_targets, key=lambda t: self.distance_to(t.rect.center))
            else:
                self.target = random.choice(possible_targets)
        else:
            self.target = None

    def move_towards_target(self, life_forms):
        # Calculate movement towards the target
        dx = self.target.rect.centerx - self.position[0]
        dy = self.target.rect.centery - self.position[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        dx, dy = dx / dist, dy / dist  # Normalize
        speed = 1 + (self.attributes['speed'] * 0.5)
        move_x = dx * speed
        move_y = dy * speed

        # Incorporate Grouping Behavior
        group_centroid = self.find_group_centroid(life_forms)
        if group_centroid:
            # Calculate direction towards group centroid
            group_dx = group_centroid[0] - self.position[0]
            group_dy = group_centroid[1] - self.position[1]
            group_dist = math.hypot(group_dx, group_dy)
            if group_dist > 0:
                group_dx, group_dy = group_dx / group_dist, group_dy / group_dist
                # Apply cohesion weight
                move_x += group_dx * COHESION_WEIGHT
                move_y += group_dy * COHESION_WEIGHT

        # Update position
        self.position[0] += move_x
        self.position[1] += move_y

        # Check collision with target
        if self.rect.colliderect(self.target.rect):
            self.interact_with_target()

    def find_group_centroid(self, life_forms):
        """
        Calculate the centroid of nearby same-type LifeForms within GROUPING_RADIUS.
        """
        nearby = []
        for lf in life_forms:
            if lf != self and lf.life_type == self.life_type and lf.alive:
                distance = self.distance_to(lf.position)
                if distance <= GROUPING_RADIUS:
                    nearby.append(lf.position)
        if nearby:
            avg_x = sum(pos[0] for pos in nearby) / len(nearby)
            avg_y = sum(pos[1] for pos in nearby) / len(nearby)
            return (avg_x, avg_y)
        return None

    def interact_with_target(self):
        if isinstance(self.target, Plant):
            self.energy += self.target.energy
            # *** Enforce the maximum energy cap ***
            if self.energy > MAX_ENERGY:
                self.energy = MAX_ENERGY
            self.target.kill()
            self.target = None
        elif isinstance(self.target, LifeForm):
            if self.target.alive:
                if self.target.life_type == self.life_type:
                    self.target = None
                    return
                # Decide to fight or flee based on intelligence
                if self.should_fight(self.target):
                    self.fight(self.target)
                else:
                    self.flee(self.target)
            else:
                self.target = None

    def should_fight(self, other):
        # Decision based on attack and defense attributes
        my_power = self.attributes['attack_power'] + self.attributes['defense']
        other_power = other.attributes['attack_power'] + other.attributes['defense']
        intelligence = self.attributes['intelligence']
        if intelligence > 0:
            return my_power >= other_power
        else:
            return random.choice([True, False])

    def fight(self, other):
        # Combat resolution
        my_attack = self.attributes['attack_power'] + random.randint(0, 5)
        other_attack = other.attributes['attack_power'] + random.randint(0, 5)
        my_defense = self.attributes['defense']
        other_defense = other.attributes['defense']

        damage_to_other = max(0, my_attack - other_defense)
        damage_to_self = max(0, other_attack - my_defense)

        self.energy -= damage_to_self
        other.energy -= damage_to_other

        if self.energy <= 0:
            self.die()
        if other.energy <= 0:
            other.die()

    def flee(self, threat):
        # Move away from the threat
        dx = self.position[0] - threat.position[0]
        dy = self.position[1] - threat.position[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        dx, dy = dx / dist, dy / dist  # Normalize
        speed = 1 + (self.attributes['speed'] * 0.5)
        self.position[0] += dx * speed
        self.position[1] += dy * speed

    def wander(self):
        # Random movement
        if random.random() < 0.1:
            self.direction += random.uniform(-0.5, 0.5)
        speed = 1 + (self.attributes['speed'] * 0.5)
        self.position[0] += math.cos(self.direction) * speed
        self.position[1] += math.sin(self.direction) * speed

    def distance_to(self, position):
        dx = self.position[0] - position[0]
        dy = self.position[1] - position[1]
        return math.hypot(dx, dy)

    def die(self):
        self.alive = False
        self.kill()

    def reproduce(self, energy_contribution):
        # Offspring inherit the same pixels with possible mutation
        new_pixels = copy.deepcopy(self.pixels)
        # Introduce mutation
        #if random.random() < MUTATION_RATE:
        #    index = random.randint(0, len(new_pixels) - 1)
        #    new_color = random.choice(list(ATTRIBUTE_COLORS.values()))
        #    new_pixels[index] = (new_pixels[index][0], new_pixels[index][1], new_color)
        #    self.image_cached = False  # Invalidate cache if mutation occurs
        offspring = LifeForm(
            life_type=self.life_type,
            position=self.position.copy(),
            pixels=new_pixels
        )
        # *** Ensure offspring's energy does not exceed MAX_ENERGY ***
        offspring.energy = min(energy_contribution, MAX_ENERGY)
        offspring.direction = random.uniform(0, 2 * math.pi)
        offspring.update_attributes()
        offspring.create_image()
        offspring.reproduction_cooldown = 0
        return offspring

# Function to load last winning parameters from CSV
def load_last_winning_parameters():
    import json
    if os.path.exists('winning_parameters.csv'):
        with open('winning_parameters.csv', 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            if rows:
                last_row = rows[-1]
                life_type = last_row['life_type']
                # Parse attributes
                attributes = {}
                for attr in ATTRIBUTE_COLORS.keys():
                    attributes[attr] = int(last_row.get(attr, 0))
                # Parse pixels
                pixels_json = last_row.get('pixels', '[]')
                pixels = json.loads(pixels_json)
                # Convert colors from lists to tuples
                pixels = [(x, y, tuple(color)) for x, y, color in pixels]
                # Compute consecutive_wins
                consecutive_wins = 1
                for row in reversed(rows[:-1]):
                    if row['life_type'] == life_type:
                        consecutive_wins += 1
                    else:
                        break
                return life_type, {'pixels': pixels, 'attributes': attributes}, consecutive_wins
    return None, None, 0

# Function to append winning parameters to CSV
def append_winning_parameters(winner_type, winning_parameters):
    import json
    file_exists = os.path.exists('winning_parameters.csv')
    with open('winning_parameters.csv', 'a', newline='') as csvfile:
        fieldnames = ['life_type', 'pixels'] + list(ATTRIBUTE_COLORS.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        row = {'life_type': winner_type}
        attributes = winning_parameters['attributes']
        for attr in ATTRIBUTE_COLORS.keys():
            row[attr] = attributes.get(attr, 0)
        # Store pixels as JSON string
        row['pixels'] = json.dumps(winning_parameters['pixels'])
        writer.writerow(row)

# Load last winning parameters before initializing the game
last_winner_type, last_winning_parameters, consecutive_wins = load_last_winning_parameters()

# Function to initialize the game
def initialize_game(winning_life_type=None, winning_parameters=None):
    global plants, life_forms, life_form_examples, games_played, last_winner_type, consecutive_wins
    games_played += 1

    # Create sprite groups
    plants = pygame.sprite.Group()
    life_forms = pygame.sprite.Group()

    # Spawn initial plants
    for _ in range(NUM_PLANTS):
        plant = Plant()
        plants.add(plant)

    # Dictionary to store parameters for each life type
    life_type_parameters = {}

    # Spawn initial life forms
    life_form_examples = {}
    if winning_life_type and winning_parameters:
        # **Subsequent Games: Retain the Winning Lifeform Type and Randomize Others**
        for life_type in life_types:
            if life_type == winning_life_type:
                # Use the winning parameters for the retained life type
                pixels = copy.deepcopy(winning_parameters['pixels'])
                attributes = copy.deepcopy(winning_parameters['attributes'])
            else:
                # Generate new random parameters for other life types
                temp_life_form = LifeForm(life_type=life_type)
                pixels = temp_life_form.generate_random_pixels()
                temp_life_form.pixels = pixels
                temp_life_form.update_attributes()
                attributes = temp_life_form.attributes.copy()

            # Ensure colors are tuples
            pixels = [(x, y, tuple(color)) for x, y, color in pixels]

            life_type_parameters[life_type] = {'pixels': pixels, 'attributes': attributes}

        # Create life forms with the stored parameters
        for life_type in life_types:
            params = life_type_parameters[life_type]
            for _ in range(NUM_EACH_LIFE_FORM):
                life_form_pixels = copy.deepcopy(params['pixels'])
                # Determine the position based on the quarter
                quarter_start, quarter_end = quarters[life_type]
                x = random.randint(quarter_start[0], quarter_end[0] - 1)
                y = random.randint(quarter_start[1], quarter_end[1] - 1)
                position = [float(x), float(y)]
                life_form = LifeForm(life_type=life_type, pixels=life_form_pixels, position=position)
                life_form.attributes = copy.deepcopy(params['attributes'])
                life_form.create_image()
                life_form.rect = life_form.image.get_rect()
                life_form.rect.center = (int(life_form.position[0]), int(life_form.position[1]))
                life_forms.add(life_form)
                if not life_form_examples.get(life_type):
                    life_form_examples[life_type] = life_form
    else:
        # **First Game: Initialize All Lifeform Types with Random Parameters**
        for life_type in life_types:
            example_life_form = None
            if life_type == 'A' and last_winning_parameters is not None:
                # Use the last winning parameters for Life Form A
                pixels = copy.deepcopy(last_winning_parameters['pixels'])
                attributes = copy.deepcopy(last_winning_parameters['attributes'])
            else:
                # Randomize parameters for this life type
                temp_life_form = LifeForm(life_type=life_type)
                pixels = temp_life_form.generate_random_pixels()
                temp_life_form.pixels = pixels
                temp_life_form.update_attributes()
                attributes = temp_life_form.attributes.copy()

            # Ensure colors are tuples
            pixels = [(x, y, tuple(color)) for x, y, color in pixels]

            life_type_parameters[life_type] = {'pixels': pixels, 'attributes': attributes}

            # Create life forms with the stored parameters
            for _ in range(NUM_EACH_LIFE_FORM):
                life_form_pixels = copy.deepcopy(life_type_parameters[life_type]['pixels'])
                # Determine the position based on the quarter
                quarter_start, quarter_end = quarters[life_type]
                x = random.randint(quarter_start[0], quarter_end[0] - 1)
                y = random.randint(quarter_start[1], quarter_end[1] - 1)
                position = [float(x), float(y)]
                life_form = LifeForm(life_type=life_type, pixels=life_form_pixels, position=position)
                life_form.attributes = copy.deepcopy(life_type_parameters[life_type]['attributes'])
                life_form.create_image()
                life_form.rect = life_form.image.get_rect()
                life_form.rect.center = (int(life_form.position[0]), int(life_form.position[1]))
                life_forms.add(life_form)
                if not life_form_examples.get(life_type):
                    life_form_examples[life_type] = life_form

def adapt_attributes(winning_parameters, life_type):
    # **Removed: Adaptation Function as Only the Winning Attributes are Carried Over**
    pass

def display_life_form_parameters():
    # Clear the screen
    screen.fill(BACKGROUND_COLOR)
    # Draw header
    header_rect = pygame.Rect(0, 0, WIDTH, HEADER_HEIGHT)
    pygame.draw.rect(screen, (50, 50, 50), header_rect)

    # Draw Quarter Boundaries with Gaps
    draw_boundary_with_gap(screen, WIDTH, HEIGHT, HEADER_HEIGHT)

    # Display life form examples with labels and parameters
    x_offset = 50
    for life_type, life_form in life_form_examples.items():
        # Draw life form image
        life_form_image = life_form.image
        image_rect = life_form_image.get_rect()
        image_rect.topleft = (x_offset, 10)
        screen.blit(life_form_image, image_rect)
        # Draw label
        label = FONT.render(f"Type {life_type}", True, (255, 255, 255))
        label_rect = label.get_rect()
        label_rect.topleft = (x_offset, image_rect.bottom + 5)
        screen.blit(label, label_rect)
        # Display attributes with colored text
        attr_y = label_rect.bottom + 5
        for attr, value in life_form.attributes.items():
            # Get the color associated with the attribute
            text_color = ATTRIBUTE_COLORS[attr]
            attr_text = FONT.render(f"{attr}: {value}", True, text_color)
            attr_rect = attr_text.get_rect()
            attr_rect.topleft = (x_offset, attr_y)
            screen.blit(attr_text, attr_rect)
            attr_y += 20
        x_offset += image_rect.width + 150  # Space between examples

    # Add "Press any key to start the game" message
    start_message = LARGE_FONT.render("Press any key to start the game", True, (255, 255, 255))
    start_rect = start_message.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(start_message, start_rect)

    pygame.display.flip()

# Helper function to determine which quarter a position is in
def determine_quarter(position):
    x, y = position
    if x < WIDTH // 2 and y < HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2:
        return 'A'  # Top Left
    elif x >= WIDTH // 2 and y < HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2:
        return 'B'  # Top Right
    elif x < WIDTH // 2 and y >= HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2:
        return 'C'  # Bottom Left
    elif x >= WIDTH // 2 and y >= HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2:
        return 'D'  # Bottom Right
    else:
        return None  # Undefined

# Function to draw boundaries with gaps
def draw_boundary_with_gap(surface, width, height, header_height, gap_ratio=0.4, line_color=(200, 200, 200), line_width=2):
    global vertical_gap_start_y, vertical_gap_end_y, horizontal_gap_start_x, horizontal_gap_end_x

    # Vertical Boundary
    vertical_x = width // 2
    vertical_start_y = header_height
    vertical_end_y = height

    total_length_v = vertical_end_y - vertical_start_y
    gap_size_v = total_length_v * gap_ratio
    gap_start_y_v = vertical_start_y + (total_length_v - gap_size_v) / 2
    gap_end_y_v = gap_start_y_v + gap_size_v

    # Store gap positions
    vertical_gap_start_y = gap_start_y_v
    vertical_gap_end_y = gap_end_y_v

    # Draw top segment of vertical boundary
    pygame.draw.line(surface, line_color, (vertical_x, vertical_start_y), (vertical_x, gap_start_y_v), line_width)
    # Draw bottom segment of vertical boundary
    pygame.draw.line(surface, line_color, (vertical_x, gap_end_y_v), (vertical_x, vertical_end_y), line_width)

    # Horizontal Boundary
    horizontal_y = header_height + (height - header_height) // 2
    horizontal_start_x = 0
    horizontal_end_x = width

    total_length_h = horizontal_end_x - horizontal_start_x
    gap_size_h = total_length_h * gap_ratio
    gap_start_x_h = (width - gap_size_h) / 2
    gap_end_x_h = gap_start_x_h + gap_size_h

    # Store gap positions
    horizontal_gap_start_x = gap_start_x_h
    horizontal_gap_end_x = gap_end_x_h

    # Draw left segment of horizontal boundary
    pygame.draw.line(surface, line_color, (horizontal_start_x, horizontal_y), (gap_start_x_h, horizontal_y), line_width)
    # Draw right segment of horizontal boundary
    pygame.draw.line(surface, line_color, (gap_end_x_h, horizontal_y), (horizontal_end_x, horizontal_y), line_width)

# Helper Function to Calculate Energy Metrics
def calculate_energy_metrics(life_forms):
    energy_metrics = {}
    for life_type in life_types:
        life_forms_of_type = [lf for lf in life_forms if lf.life_type == life_type and lf.alive]
        total_energy = sum(lf.energy for lf in life_forms_of_type)
        average_energy = total_energy / len(life_forms_of_type) if life_forms_of_type else 0
        energy_metrics[life_type] = {'total': total_energy, 'average': average_energy}
    return energy_metrics

def main():
    global last_winner_type, consecutive_wins, last_winning_parameters

    # Initialize the game for the first time
    initialize_game()
    waiting_to_start = True
    start_time = pygame.time.get_ticks()
    waiting_for_restart = False
    winner_declared = False
    winner_screen_start_time = None

    # Plant respawn event
    PLANT_RESPAWN_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(PLANT_RESPAWN_EVENT, PLANT_RESPAWN_TIME)

    # Main game loop
    running = True
    while running:
        clock.tick(60)  # Limit to 60 FPS
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if waiting_to_start:
                if event.type == pygame.KEYDOWN:
                    waiting_to_start = False
            elif waiting_for_restart:
                if event.type == pygame.KEYDOWN:
                    winner_declared = False
                    waiting_for_restart = False
                    initialize_game(winning_life_type=winner_type, winning_parameters=winning_parameters)
                    waiting_to_start = True
                    start_time = pygame.time.get_ticks()
                    winner_screen_start_time = None
            else:
                # Handle game events
                if event.type == PLANT_RESPAWN_EVENT:
                    if len(plants) < MAX_PLANTS:
                        plant = Plant()
                        plants.add(plant)

        if waiting_to_start:
            display_life_form_parameters()
            # *** Automatically start the game after 10 seconds ***
            if current_time - start_time >= 10000:
                waiting_to_start = False
        elif not waiting_for_restart and not winner_declared:
            # Update life forms
            for life_form in life_forms.copy():
                life_form.update(plants, life_forms)
                if not life_form.alive:
                    life_forms.remove(life_form)

            # Check if only one type of life form remains
            life_types_remaining = set(lf.life_type for lf in life_forms)
            if len(life_types_remaining) == 1 and len(life_forms) > 0:
                winner_type = life_types_remaining.pop()
                winner_declared = True
                # Capture the winning life form's parameters
                for life_form in life_forms:
                    if life_form.life_type == winner_type:
                        winning_life_form = life_form
                        break
                # Store the winning parameters
                winning_parameters = {
                    'pixels': winning_life_form.pixels,
                    'attributes': winning_life_form.attributes
                }
                # Update last winner and consecutive wins
                if last_winner_type == winner_type:
                    consecutive_wins += 1
                else:
                    consecutive_wins = 1
                    last_winner_type = winner_type
                # Append winning parameters to CSV file
                append_winning_parameters(winner_type, winning_parameters)
                # Calculate average attributes of the winner
                total_attributes = Counter()
                num_winners = 0
                for life_form in life_forms:
                    if life_form.life_type == winner_type:
                        total_attributes.update(life_form.attributes)
                        num_winners += 1
                # Calculate average attributes
                average_attributes = {attr: total_attributes[attr] / num_winners for attr in total_attributes}
                # Start timing the winner screen
                winner_screen_start_time = current_time
                # Display winner information
                winner_message = f"The Winner Is Type {winner_type}!"
                waiting_for_restart = True

        elif waiting_for_restart:
            # *** Automatically restart the game after 10 seconds ***
            if winner_screen_start_time and (current_time - winner_screen_start_time >= 10000):
                winner_declared = False
                waiting_for_restart = False
                initialize_game(winning_life_type=winner_type, winning_parameters=winning_parameters)
                waiting_to_start = True
                start_time = pygame.time.get_ticks()
                winner_screen_start_time = None

        # Draw everything
        if waiting_to_start:
            pass
        elif waiting_for_restart:
            # Display the winner message and wait for keypress or 10 seconds
            screen.fill(BACKGROUND_COLOR)
            # Create a semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT - HEADER_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, HEADER_HEIGHT))

            # Display winner message
            winner_text = LARGE_FONT.render(winner_message, True, (255, 255, 255))
            winner_rect = winner_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(winner_text, winner_rect)

            # Display average attributes with colored text
            attr_y = winner_rect.bottom + 20
            for attr, value in average_attributes.items():
                text_color = ATTRIBUTE_COLORS[attr]
                attr_text = FONT.render(f"{attr}: {value:.2f}", True, text_color)
                attr_rect = attr_text.get_rect(center=(WIDTH // 2, attr_y))
                screen.blit(attr_text, attr_rect)
                attr_y += 30

            # Instruction to restart
            instruction_text = FONT.render("Press any key to restart the game.", True, (255, 255, 255))
            instruction_rect = instruction_text.get_rect(center=(WIDTH // 2, attr_y + 30))
            screen.blit(instruction_text, instruction_rect)
        else:
            # Draw the game as usual
            screen.fill(BACKGROUND_COLOR)
            # Draw header
            header_rect = pygame.Rect(0, 0, WIDTH, HEADER_HEIGHT)
            pygame.draw.rect(screen, (50, 50, 50), header_rect)

            # Draw Quarter Boundaries with Gaps
            draw_boundary_with_gap(screen, WIDTH, HEIGHT, HEADER_HEIGHT)

            # Calculate Energy Metrics
            energy_metrics = calculate_energy_metrics(life_forms)

            # Draw sprites
            plants.draw(screen)
            life_forms.draw(screen)

            # Draw games played counter in top right of header
            games_played_text = FONT.render(f"Games Played: {games_played}", True, (255, 255, 255))
            games_played_rect = games_played_text.get_rect()
            games_played_rect.topright = (WIDTH - 20, 10)
            screen.blit(games_played_text, games_played_rect)

            # Display Last Winner
            if last_winner_type is not None:
                last_winner_text = FONT.render(f"Last Winner: {last_winner_type}", True, (255, 255, 255))
                last_winner_rect = last_winner_text.get_rect()
                last_winner_rect.topright = (WIDTH - 20, games_played_rect.bottom + 5)
                screen.blit(last_winner_text, last_winner_rect)

                # Display Wins
                wins_text = FONT.render(f"Wins: {consecutive_wins}", True, (255, 255, 255))
                wins_rect = wins_text.get_rect()
                wins_rect.topright = (WIDTH - 20, last_winner_rect.bottom + 5)
                screen.blit(wins_text, wins_rect)

            # Calculate font height
            font_height = FONT.get_height()

            # Determine how many attributes per column
            attributes_per_column = len(ATTRIBUTE_COLORS) // 2 + len(ATTRIBUTE_COLORS) % 2

            # Calculate total height required for the first column
            total_column_height = attributes_per_column * font_height

            # Calculate starting positions for the columns, moved 300 pixels to the right
            start_y = max((HEADER_HEIGHT - total_column_height) // 2, 0)
            column1_x = WIDTH // 2 - 100 + 300  # Adjust X position for the first column, moved 300 pixels to the right
            column2_x = WIDTH // 2 + 100 + 300  # Adjust X position for the second column, moved 300 pixels to the right

            # Render the first column
            attribute_y_offset = start_y
            for i, (attr, color) in enumerate(list(ATTRIBUTE_COLORS.items())[:attributes_per_column]):
                # Create text for the attribute name with the associated color
                attribute_text = FONT.render(attr.capitalize(), True, color)
                attribute_rect = attribute_text.get_rect()
                attribute_rect.centerx = column1_x  # Position in the first column, moved 300 pixels to the right
                attribute_rect.y = attribute_y_offset
                screen.blit(attribute_text, attribute_rect)
                attribute_y_offset += font_height  # Increment Y offset by the font height

            # Render the second column
            attribute_y_offset = start_y
            for i, (attr, color) in enumerate(list(ATTRIBUTE_COLORS.items())[attributes_per_column:]):
                # Create text for the attribute name with the associated color
                attribute_text = FONT.render(attr.capitalize(), True, color)
                attribute_rect = attribute_text.get_rect()
                attribute_rect.centerx = column2_x  # Position in the second column, moved 300 pixels to the right
                attribute_rect.y = attribute_y_offset
                screen.blit(attribute_text, attribute_rect)
                attribute_y_offset += font_height  # Increment Y offset by the font height

            # Draw life form examples and energy metrics in header
            x_offset = 50
            for life_type, life_form in life_form_examples.items():
                # Draw life form image
                life_form_image = life_form.image
                image_rect = life_form_image.get_rect()
                image_rect.topleft = (x_offset, 10)
                screen.blit(life_form_image, image_rect)
                # Draw label
                label = FONT.render(f"Type {life_type}", True, (255, 255, 255))
                label_rect = label.get_rect()
                label_rect.topleft = (x_offset, image_rect.bottom + 5)
                screen.blit(label, label_rect)

                # Display Total and Average Energy
                total_energy = energy_metrics[life_type]['total']
                average_energy = energy_metrics[life_type]['average']

                # Render Total Energy
                total_energy_text = FONT.render(f"Total Energy: {total_energy:.0f}", True, (255, 255, 255))
                total_energy_rect = total_energy_text.get_rect()
                total_energy_rect.topleft = (x_offset, label_rect.bottom + 5)
                screen.blit(total_energy_text, total_energy_rect)

                # Render Average Energy
                average_energy_text = FONT.render(f"Avg Energy: {average_energy:.0f}", True, (255, 255, 255))
                average_energy_rect = average_energy_text.get_rect()
                average_energy_rect.topleft = (x_offset, total_energy_rect.bottom + 5)
                screen.blit(average_energy_text, average_energy_rect)

                x_offset += image_rect.width + 150  # Space between examples

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
