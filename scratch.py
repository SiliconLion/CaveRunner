import pygame
import socket

# Global constants

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
PURPLE = (255, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

def send_level(level):

    str_walls = ''
    str_stalactites = ''
    for e in level.walls:
        str_walls = str_walls + str(e[0]) + ","
        str_walls = str_walls + str(e[1]) + ","
    for e in level.stalactites:
        str_stalactites = str_stalactites + str(e[0]) + ","
        str_stalactites = str_stalactites + str(e[1]) + ","

    #send the walls,
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(str_walls.encode())
    s.close()

    #send the stalactites
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(str_stalactites.encode())
    s.close()

def send_update(str_x, str_y, should_send_level, level):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    message = str_x +',' + str_y + ',' + str(should_send_level)
    s.sendall(message.encode())
    s.close()

    if should_send_level == True:
        send_level(level)

def recv_render():
    # try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        myfile = open("render.bmp", "wb")
        # received = ''
        while True:
            # print('started trying to recive')
            data = s.recv(4096)
            # print('recved')
            if not data:
                # print("end of received transmission")
                break
            else:
                # print(data)
                # received = received + str(data)
                myfile.write(data)
            # print("looping")
    # finally:
    #     print('asdfasdfasdfasdfasdf')




class Player(pygame.sprite.Sprite):
    """
    This class represents the bar at the bottom that the player controls.
    """

    # -- Methods
    def __init__(self):
        """ Constructor function """

        # Call the parent's constructor
        super().__init__()

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        width = 50
        height = 50
        self.image = pygame.Surface([width, height])
        self.image.fill(WHITE)

        # Set a reference to the image rect.
        self.rect = self.image.get_rect()

        # Set speed vector of player
        self.change_x = 0
        self.change_y = 0

        # List of sprites we can bump against
        self.level = None

    def update(self):
        """ Move the player. """
        # Gravity
        self.calc_grav()

        # Move left/right
        self.rect.x += self.change_x

        # See if we hit anything
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:
            # If we are moving right,
            # set our right side to the left side of the item we hit
            if self.change_x > 0:
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                # Otherwise if we are moving left, do the opposite.
                self.rect.left = block.rect.right

        # Move up/down
        self.rect.y += self.change_y

        # Check and see if we hit anything
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:

            # Reset our position based on the top/bottom of the object.
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom

            # Stop our vertical movement
            self.change_y = 0

    def calc_grav(self):
        """ Calculate effect of gravity. """
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += .35

        # See if we are on the ground.
        if self.rect.y >= SCREEN_HEIGHT - self.rect.height and self.change_y >= 0:
            self.change_y = 0
            self.rect.y = SCREEN_HEIGHT - self.rect.height

    def jump(self):
        """ Called when user hits 'jump' button. """

        # move down a bit and see if there is a platform below us.
        # Move down 2 pixels because it doesn't work well if we only move down 1
        # when working with a platform moving down.
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        self.rect.y -= 2

        # If it is ok to jump, set our speed upwards
        if len(platform_hit_list) > 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.change_y = -10

    # Player-controlled movement:
    def go_left(self):
        """ Called when the user hits the left arrow. """
        self.change_x = -6

    def go_right(self):
        """ Called when the user hits the right arrow. """
        self.change_x = 6

    def stop(self):
        """ Called when the user lets off the keyboard. """
        self.change_x = 0


class Platform(pygame.sprite.Sprite):
    """ Platform the user can jump on """

    def __init__(self, width, height):
        """ Platform constructor. Assumes constructed with user passing in
            an array of 5 numbers like what's defined at the top of this code.
            """
        super().__init__()

        self.image = pygame.Surface([width, height])
        self.image.fill(WHITE)

        self.rect = self.image.get_rect()


class Level():
    """ This is a generic super-class used to define a level.
        Create a child class for each level with level-specific
        info. """

    def __init__(self, player):
        """ Constructor. Pass in a handle to player. Needed for when moving
            platforms collide with the player. """
        self.platform_list = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        self.player = player

        # How far this world has been scrolled left/right
        self.world_shift = 0

    # Update everything on this level
    def update(self):
        """ Update everything in this level."""
        self.platform_list.update()
        self.enemy_list.update()

    def draw(self, screen):
        """ Draw everything on this level. """

        # Draw the background
        screen.fill(BLACK)

        # Draw all the sprite lists that we have
        self.platform_list.draw(screen)
        self.enemy_list.draw(screen)

    def shift_world(self, shift_x):
        """ When the user moves left/right and we need to scroll
        everything: """

        # Keep track of the shift amount
        self.world_shift += shift_x

        # Go through all the sprite lists and shift
        for platform in self.platform_list:
            platform.rect.x += shift_x

        for enemy in self.enemy_list:
            enemy.rect.x += shift_x


# Create platforms for the level
class Level_01(Level):
    """ Definition for level 1. """

    def __init__(self, player):
        """ Create level 1. """

        # Call the parent constructor
        Level.__init__(self, player)

        self.level_limit = -1000
        self.walls = []
        self.stalactites = []

        # Array with width, height, x, and y of platform
        level = []
        for i in range(2800//50):
            level.append([50,50, 50*i, 0])
            self.walls.append([50*i, 0])
        for i in range(600//50):
            level.append([50,50,0, 50*i])
            self.walls.append([0, 50*i])
        for i in range(400//50):
            level.append([50, 50, 50+50*i, 550])
            self.walls.append([50+50*i, 550])
        for i in range(2):
            for j in range(600//50):
                level.append([50,50,600+50*j, 500+ 50*i])
                self.walls.append([600+50*j, 500+ 50*i])
        for i in range(800//50):
            level.append([50,50,1400+50*i,550])
            self.walls.append([1400+50*i,550])
        level.append([50, 50, 950, 50])
        self.stalactites.append([950, 50])
        level.append([50, 50, 1300, 50])
        self.stalactites.append([1300, 50])
        level.append([50, 50, 1550, 50])
        self.stalactites.append([1550, 50])
        level.append([50, 50, 1800, 50])
        self.stalactites.append([1800, 50])



        # level = [[2800, 50, 0, 0],
        #          [50, 600, 0, 0],
        #          [400, 50, 50, 550], [600, 100, 600, 500], [800, 50, 1400, 550],
        #          [50, 50, 950, 50], [50, 50, 1300, 50], [50, 50, 1550, 0], [50, 50, 1800, 50]
        #          ]

        # Go through the array above and add platforms
        for platform in level:
            block = Platform(platform[0], platform[1])
            block.rect.x = platform[2]
            block.rect.y = platform[3]
            block.player = self.player
            self.platform_list.add(block)


# Create platforms for the level
class Level_02(Level):
    """ Definition for level 2. """

    def __init__(self, player):
        """ Create level 1. """

        # Call the parent constructor
        Level.__init__(self, player)

        self.level_limit = -1000
        self.walls = []
        self.stalactites = []

        level = []
        # Array with type of platform, and x, y location of the platform.
        for i in range(2800 // 50):
            level.append([50, 50, 50 * i, 0])
            self.walls.append([50 * i, 0])
        for i in range(600 // 50):
            level.append([50, 50, 0, 50 * i])
            self.walls.append([0, 50 * i])
        for i in range(400 // 50):
            level.append([50, 50, 50 + 50 * i, 550])
            self.walls.append([50 + 50 * i, 550])
        for i in range(2):
            for j in range(600 // 50):
                level.append([50, 50, 600 + 50 * j, 500 + 50 * i])
                self.walls.append([600 + 50 * j, 500 + 50 * i])
        for i in range(3):
            for j in range(800//50):
                level.append([50,50,1400+50*j,450+50*i])
                self.walls.append([1400+50*j,450+50*i])
        level.append([50, 50, 950, 50])
        self.stalactites.append([950, 50])
        level.append([50, 50, 1300, 50])
        self.stalactites.append([1300, 50])
        level.append([50, 50, 1550, 50])
        self.stalactites.append([1550, 50])
        level.append([50, 50, 1800, 50])
        self.stalactites.append([1800, 50])

        # level = [[2800, 50, 0, 0],
        #          [400, 50, 50, 550], [600, 100, 600, 500], [800, 1500, 1400, 450],
        #          [50, 50, 500, 50], [50, 50, 950, 50], [50, 50, 1300, 50], [50, 50, 1550, 0], [50, 50, 1800, 50]
        #          ]

        # Go through the array above and add platforms
        for platform in level:
            block = Platform(platform[0], platform[1])
            block.rect.x = platform[2]
            block.rect.y = platform[3]
            block.player = self.player
            self.platform_list.add(block)


def main():
    """ Main Program """
    pygame.init()

    # Set the height and width of the screen
    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("Cave Runner")

    # Create the player
    player = Player()

    # Create all the levels
    level_list = []
    level_list.append(Level_01(player))
    level_list.append(Level_02(player))

    # Set the current level
    current_level_no = 0
    current_level = level_list[current_level_no]

    active_sprite_list = pygame.sprite.Group()
    player.level = current_level

    player.rect.x = 200
    player.rect.y = 500
    active_sprite_list.add(player)

    # Loop until the user clicks the close button.
    done = False

    # Used to manage how fast the screen updates
    clock = pygame.time.Clock()
    gameDisplay = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))



    # gameImg = pygame.image.load('insertimagehere.png')

    def image(display):
        gameImg = pygame.image.load('render.bmp')
        display.blit(gameImg, (0, 0))


    # -------- Main Program Loop -----------
    should_send_level = True

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player.go_left()
                if event.key == pygame.K_RIGHT:
                    player.go_right()
                if event.key == pygame.K_UP:
                    player.jump()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT and player.change_x < 0:
                    player.stop()
                if event.key == pygame.K_RIGHT and player.change_x > 0:
                    player.stop()

        # Update the player.
        active_sprite_list.update()

        # Update items in the level
        current_level.update()

        # If the player gets near the right side, shift the world left (-x)
        if player.rect.right >= 500:
            diff = player.rect.right - 500
            player.rect.right = 500
            current_level.shift_world(-diff)

        # If the player gets near the left side, shift the world right (+x)
        if player.rect.left <= 120:
            diff = 120 - player.rect.left
            player.rect.left = 120
            current_level.shift_world(diff)

        # If the player gets to the end of the level, go to the next level
        current_position = player.rect.x + current_level.world_shift
        if current_position < current_level.level_limit:
            player.rect.x = 120
            if current_level_no < len(level_list) - 1:
                current_level_no += 1
                current_level = level_list[current_level_no]
                player.level = current_level
                should_send_level = True


        # #NETWORKING STUFF BELOW

        playerx = str(player.rect.x)
        playery = str(player.rect.y)

        # should_send_level = False
        send_update(playerx, playery, should_send_level, current_level)
        should_send_level = False

        recv_render()

        # #sends the sprite positions
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        #     s.connect((HOST, PORT))
        #
        # #recivces the rendered image
        # myfile = open("render.bmp", "wb+")
        # while True:
        #     data = s.recv(4096)
        #     if not data:
        #         print("end of received transmission")
        #         break
        #     else:
        #         # received = received + str(data)
        #         myfile.write(data)
        #


        # #NETWORKING STUFF ABOVE

        # ALL CODE TO DRAW SHOULD GO BELOW THIS COMMENT

        # current_level.draw(screen)
        # active_sprite_list.draw(screen)
        #gameDisplay.fill(WHITE)
        #image()
        image(gameDisplay)


        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT

        # Limit to 60 frames per second
        clock.tick(60)

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

    # Be IDLE friendly. If you forget this line, the program will 'hang'
    # on exit.
    pygame.quit()


if __name__ == "__main__":
    main()