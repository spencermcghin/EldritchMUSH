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

    def hasBow(self, message):
        right_hand = self.parent.getRightHand()

        if (right_hand == self.parent.getLeftHand()) and right_hand.db.is_bow:
            return right_hand

        if message:
            self.parent.message(message)

        return None

    def useArrows(self, value = 1):
        arrows = self.caller.db.arrow_slot[0]
        arrows.db.quantity += value

    @property
    def arrowQuantity(self):
        arrows = self.caller.db.arrow_slot[0]
        return arrows.db.quantity

    @property
    def hasArrowsEquipped(self):
        return True if self.caller.db.arrow_slot else False

    @property
    def hasArrowsLeft(self):
        if self.hasArrowsEquipped:
            arrows = self.caller.db.arrow_slot[0]
            arrow_qty = arrows.db.quantity
            if arrow_qty > 0:
                return True

        return False