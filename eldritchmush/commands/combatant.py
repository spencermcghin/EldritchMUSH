from commands.combat import Helper

class Combatant:
    """
    A helper class used to ease readability and flow of combat functions
    Should be rewritten ultimately to use properties/getters/setters
    """

    def __init__(self, caller):
        self.caller = caller
        self.helper = Helper(caller)

    def canFight(self):
        return self.helper.canFight(self.caller)

    def cantFight(self):
        return not self.canFight()

    def message(self,msg):
        self.caller.msg(msg)

    def debugMessage(self,msg):
        #Is there a way we can broadcast this only to admins?
        self.caller.msg(msg)

    def broadcast(self, msg):
        self.caller.location.msg_contents(msg)

    def hasTurn(self):
        return self.caller.db.combat_turn

    def medicine(self):
        return self.caller.db.medicine

    def battlefieldMedicine(self):
        return self.caller.db.battlefieldmedicine

    def body(self):
        return self.caller.db.body

    def addBody(self, value):
        self.caller.db.body += 1

    def name(self):
        return self.caller.key

    def bleedPoints(self):
        return self.caller.db.bleed_points

    def resilience(self):
        return self.caller.db.resilience

    def atMaxBleedPoints(self):
        return self.bleedPoints() == self.totalBleedPoints()

    #TODO: Magic Number?
    def totalBleedPoints(self):
        return self.resilience() + 3

    #Syntactic Sugar
    def hasMoreBodyThan(self, value):
        return self.body() > value

    def hasBody(self, value):
        return self.body() == value

    def hasBleedPoints(self):
        return self.bleedPoints() > 0

    def setBody(self, value):
    def setBody(self, value):
        self.caller.db.body = value

    #TODO: Do we have a max body we should account for here?
    def addBody(self, value):
        self.caller.db.body += value

    #TODO: How do we account for max bleed points here?
    def addBleedPoints(self, value):
        self.caller.db.bleed_points += value


