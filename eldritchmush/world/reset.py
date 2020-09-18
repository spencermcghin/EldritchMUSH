from typeclasses.characters import Character

def reset_runner():
    # Get all characters
    c = Character()
    characters = [character for character in c.objects.all()]
    print(characters)
    # for character in characters:
    #     character.reset_stats()

if __name__ == "__main__":
    reset_runner()
