from typeclasses.characters import Character

def reset_runner():
    # Get all characters
    characters = [character for character in Character.objects.all()]

    for character in characters:
        character.reset_stats()

if __name__ == "__main__":
    reset_runner()
