
"""
The classic game of flappy bird. Make with python
and pygame. Features pixel perfect collision using masks :o
"""

import pygame
import neat
import time
import os
import random
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = 0

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),\
            pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),\
            pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans",50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5  #time for the animation of the bird

    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count =0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5        #negative to move up
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        d = self.vel*self.tick_count + 1.5*self.tick_count**2
        if d >= 16:
            d=16    #don't jump to high
        if d < 0:
            d-=2
        self.y = self.y + d
        if d<0 or self.y<self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
            else:
                if self.tilt > -90:
                    self.tilt -= self.ROT_VEL

    def draw(self,win):
        self.img_count +=1
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 +1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        #rotate the image
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft= (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)       #blit = draw image

    def get_mask(self):
        return pygame.mask.from_surface(self.img)      #mask used for pixel perfect collision

class Pipe:
    GAP = 200
    VEL = 5         #the bird doesn't not move left and right; pipes only move to the left

    def __init__(self,x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG,False,True)     #flip the one pipe image so it looks like upside down
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50,450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self,win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        #offset: how far away are the objects
        top_offset = (self.x - bird.x, self.top - round(bird.x))
        bottom_offset = (self.x -bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)     # returns none if they don't collide
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self,y):
        self.y = y
        # two base images; one after another
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        move floor so it looks like its scrolling
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # base moves from right to left
        # use two images and set them on after another
        # when one images gets of the screen (left side), move it the right and let it move to the left again
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMG, (0,0))  #blit = draw image
    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(),10))

    text = STAT_FONT.render("Gen: " + str(gen),1,(255,255,255))
    win.blit(text, (10,10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    pygame.display.update()

def main(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []  #run all the birds (set in neat) at the same time

    for _,g in genomes:     #genome is a tuple (1,obj)
        #one net, bird and genome belonging together
        net = neat.nn.FeedForwardNetwork.create(g,config)
        nets.append(net)
        birds.append(Bird(230,250))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:   #if there is no birds left quit the game
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            #encourage the bird to move forward and not to fly off the screen by giving fitness per second alive
            ge[x].fitness += 0.1
            #get the result of the net for this bird
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), \
                                       abs(bird.y - pipes[pipe_ind].bottom)))
            #evaluate the output from the net
            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                # what happens when bird and pipe collide
                if pipe.collide(bird):
                    # if a bird hits a pipe it looses a fitness level
                    ge[x].fitness -=1
                    # remove bird, net and genome when collides from further processing
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            # remove pipe once it's off the screen and create a new one from the right
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score +=1
            # encourage birds to go through pipes not crash into it by giving it extra score
            for g in ge:
                g.fitness +=5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            #check if bird hits the base
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win,birds, pipes, base, score, GEN)

def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)
    p = neat.Population(config)
    #print out statistics
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main,50) #call the main func 50 times; use main as the fitness func


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)




