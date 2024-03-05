from sbs_utils.objects import Npc
from sbs_utils.agent import Agent, get_story_id
from sbs_utils.mast.label import label
from sbs_utils.tickdispatcher import TickDispatcher
from sbs_utils.procedural.execution import task_schedule, jump, AWAIT, get_variable
from sbs_utils.procedural.timers import delay_sim
from sbs_utils.procedural.query import to_object, to_id, object_exists
from sbs_utils.procedural.space_objects import target, closest, clear_target, closest_list
from sbs_utils.procedural.roles import role
from sbs_utils.procedural.science import science_set_scan_data
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils import faces
from sbs_utils.vec import Vec3



from enum import IntEnum
from random import randint
import sbs
from sbs_utils.procedural.routes import RouteSpawn, RouteDamageObject, RouteCommsSelect, RouteCommsMessage

class Fleet(Agent):
    #--------------------------------------------------------------------------------------
    def __init__(self, position, side):
        super().__init__()

        self.id = get_story_id()
        self.add()
        self.side = side
        self.position = Vec3(position.x, position.y, position.z) #Vec3(0,0,0)
        self.destination = Vec3(0,0,0)
        self.anger_dict = {}
        self.add_role("fleet")

        if side is not None:
            if isinstance(side, str):
                roles = side.split(",")
            else:
                roles = side
            side = roles[0].strip()
            if side != "#":
#                obj.side = side
                self.side = side
#            self.update_comms_id()
            for role in roles:
                self.add_role(role)

        task_schedule(self.tick)

#        self.set_inventory_value("anger_map",{})
#        self.set_link_value("ship_list",{})

    #--------------------------------------------------------------------------------------
    @label()
    def tick(self):
        #get average center of all my ships
        #self.add_link("ship_list", ship_id)
        #self.remove_link("ship_list", ship_id)

        ship_set = self.get_link_objects("ship_list")
        if len(ship_set) < 1:
            yield AWAIT(delay_sim(seconds=5))
            yield jump(self.tick)

        average = Vec3(0,0,0)
        for e in ship_set:
            if object_exists(e):
                average.x += e.engine_object.pos.x
                average.y += e.engine_object.pos.y
                average.z += e.engine_object.pos.z
            else:
                # cull this object from the linked objects
                self.remove_link("ship_list", e.id)

        average /= len(ship_set)

        #that's my point
        self.position = average

        use_path = False

        #--------------------------------------------------------------------
        #move my point in the direction I want to go (perhaps 1000m?)

        difference = Vec3(self.destination) - Vec3(self.position)
        if difference.length() > 3000:
            use_path = True
        difference = difference.unit()
        difference *= 1000
        self.position += difference


        #--------------------------------------------------------------------
        # am I angry at someone?
        best_id = None
        best_anger = 0
        for e in self.anger_dict:
            that_anger = self.anger_dict[e]
            if best_anger < that_anger:
                best_anger = that_anger
                best_id = e
            self.anger_dict[e] = max(0,that_anger-1) # reduce heat over time

        if None != best_id:   # someone to be angry at
            # if so, we should move towards him
            enemy = Agent.get(best_id)
            if None != enemy:
                self.position = enemy.pos
                use_path = False

        #--------------------------------------------------------------------
        # if it's time, find a path




        #--------------------------------------------------------------------
        #tell all my ships to go to that point (and go throttle 1.0)
        for e in ship_set:
            blob = e.data_set
            blob.set("target_pos_x", self.position.x,0)
            blob.set("target_pos_y", self.position.y,0)
            blob.set("target_pos_z", self.position.z,0)

            diff = Vec3(e.engine_object.pos) - self.position
            if diff.length() < 500:
                blob.set("throttle", 0.0,0)
            else:
                blob.set("throttle", 1.0,0)

        #--------------------------------------------------------------------
        # find target to move to and attack

        # Look for a station near 
        the_target = None
        if the_target is None:
            the_target = closest(ship_set[0], role("Station") & role("tsn"), 3000)

        # Look for a player near 
        if the_target is None:
            the_target = closest(ship_set[0], role("PlayerShip"), 3000)

        # Otherwise look for a tsn station
        if the_target is None:
            the_target = closest(ship_set[0], role("Station") & role("tsn"))

        # If any of these check resulted in a target
        if the_target is not None:
            distance = sbs.distance_id(to_id(ship_set[0]), to_id(the_target))
            self.destination = Vec3(to_object(the_target).engine_object.pos)

            for e in ship_set:
                blob = e.data_set
                blob.set("target_id", the_target.id,0)

        yield AWAIT(delay_sim(seconds=10))
        yield jump(self.tick)

    #--------------------------------------------------------------------------------------
    def ship_takes_damage(self, my_ship_id, attacker_id):
        self.anger_dict[attacker_id] = 100  # how long I will be angry

#--------------------------------------------------------------------------------------
@RouteDamageObject 
def ship_takes_damage():#event):
    event = get_variable("EVENT")
    attacker_id = event.origin_id
    victim_id = event.selected_id
    my_fleet = to_object(get_inventory_value(victim_id, "my_fleet_id"))
    if None != my_fleet:
        my_fleet.ship_takes_damage(victim_id, attacker_id)

#--------------------------------------------------------------------------------------
def fleet_spawn(position, side):
    return Fleet(position, side)




"""

Fleet

contains a list of ships that belong to it
position
destination
path to target
anger management



Tick()
get average center of all my ships
that's my point
move my point in the direction I want to go (perhaps 1000m?)
tell all my ships to go to that point (and go throttle 1.0)

make decisions about where the fleet goes
	naviagitn ghte existing path
	refreshing a stale path

reduce all heats by 1

anger:
ship takes damage from emeny:
	set enemy heat to 100

if best heat > 0
	tell all ships to move to and attack heat target


"""