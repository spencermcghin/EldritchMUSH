from commands.combat import Helper

class Inventory:
    """
    A helper class used to ease readability and flow of combat functions
    Should be rewritten ultimately to use properties/getters/setters
    """

    def __init__(self, parent, caller):
        self.caller = caller
        self.parent = parent


    def getWeapon(self):
        right_hand = self.parent.getRightHand()
        left_hand = self.parent.getLeftHand()
        if right_hand.db.damage >= 0:
            return right_hand
        elif left_hand.db.damage >= 0:
            return left_hand
        else:
            return None

    def getBow(self, message):
        right_hand = self.parent.getRightHand()

        if (right_hand == self.parent.getLeftHand()) and right_hand.db.is_bow:
            return right_hand

        if message:
            self.parent.message(message)

        return None

