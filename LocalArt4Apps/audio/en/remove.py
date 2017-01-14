import os

sounds = ['angel.png', 'blue.png', 'high.png', 'chick.png', 'wet.png', 'upper_P.png', 'question.png', 'upper_W.png', 'fun.png', 'ground.png', 'mask.png', 'dress.png', 'hole.png', 'juice.png', 'bug.png', 'color.png', 'blind.png', 'on.png', 'food.png', 'prince.png', 'wind.png', 'vet.png', 'hike.png', 'teacher.png', 'wheel.png']

for f in os.listdir("."):
    if not f in sounds:
        os.remove(f)
