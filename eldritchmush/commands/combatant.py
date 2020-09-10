from commands.combat import Helper
from typeclasses.characters import Character

class Combatant:
    """
    A helper class used to ease readability and flow of combat functions
    Should be rewritten ultimately to use properties/getters/setters
    """

    def __init__(self, caller):
        self.caller = caller
        self.helper = Helper(caller)
        self.name = self.caller.key

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

    def hasTurn(self,message=None):
        if message and not self.caller.db.combat_turn:
            self.message(message)
        return self.caller.db.combat_turn

    def stabilize(self):
        return self.caller.db.stabilize

    def hasStabilize(self,message=None):
        if message and not self.caller.db.stabilize:
            self.message(message)
        return self.stabilize()

    def medicine(self):
        return self.caller.db.medicine

    def battlefieldMedicine(self):
        return self.caller.db.battlefieldmedicine

    #Syntactic Sugar
    def hasMoreBodyThan(self, value):
        return self.body() > value

    def hasBody(self, value = None):
        if value:
            return self.body() == value
        return self.body() > 0


    def setBody(self, value):
        self.caller.db.body = value

    def addBody(self, value):
        if (self.caller.db.body + value) <= 3:
            self.caller.db.body += value
        else:
            self.setBody(3)

    def body(self):
        #self.caller.message(f"Debug body is {self.caller.db.body}")
        return self.caller.db.body

    def resilience(self):
        return self.caller.db.resilience

    def bleedPoints(self):
        return self.caller.db.bleed_points

    def atMaxBleedPoints(self):
        return self.bleedPoints() == self.totalBleedPoints()

    #TODO: Magic Number?
    def totalBleedPoints(self):
        return self.resilience() + 3

    def missingBleedPoints(self):
        return self.totalBleedPoints() - self.bleedPoints()

    def hasBleedPoints(self):
        return self.bleedPoints() > 0

    def setBleedPoints(self, value):
        self.caller.db.bleed_points = value

    def addBleedPoints(self, value):
        if (self.caller.db.bleed_points + value) <= self.totalBleedPoints():
            self.caller.db.bleed_points += value
        else:
            self.resetBleedPoints()

    def resetBleedPoints(self):
        self.setBleedPoints(self.totalBleedPoints())

    def isAtMaxDeathPoints(self):
        return self.deathPoints() >= 3

    def addDeathPoints(self, value):
        if (self.deathPoints() + value) <= 3:
            self.caller.db.death_points += value
        else:
            self.setDeathPoints(3)

    def setDeathPoints(self, value):
        self.caller.db.death_points = value

    def hasDeathPoints(self, value = None):
        if value:
            return self.deathPoints() == value
        return self.deathPoints() > 0

    def missingDeathPoints(self):
        return 3 - self.deathPoints()

    def deathPoints(self):
        return self.caller.db.death_points

    def chirurgeon(self):
        return self.caller.db.chirurgeon

    def inCombat(self):
        return self.caller.db.in_combat

    def secondsUntilNextChirurgery(self, current_time):
        if not self.caller.db.last_chirurgery:
            return 0
        else:
            seconds_since_last_chirurgery = (int(current_time) - int(self.caller.db.last_chirurgery))
            return 900 - seconds_since_last_chirurgery

    def setChirurgeryTimer(self,current_time):
        self.caller.db.last_chirurgery = current_time


    def resetTough(self):
        self.caller.db.tough = self.caller.db.total_tough

    def removeWeakness(self):
        self.caller.db.weakness = 0
