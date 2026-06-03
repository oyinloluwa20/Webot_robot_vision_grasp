    
    
from controller import Robot, Camera, Motor

robot = Robot()
TIME_STEP = int(robot.getBasicTimeStep())
MAX_SPEED = 6.28

camera = robot.getDevice("camera")
camera.enable(TIME_STEP)
camera.recognitionEnable(TIME_STEP)

gripper_arm = robot.getDevice("horizontal_motor") 
gripper_finger_left = robot.getDevice("finger_motor::left")  
gripper_finger_right = robot.getDevice("finger_motor::right")  

left_motor = robot.getDevice("left wheel motor")
right_motor = robot.getDevice("right wheel motor")
left_motor.setPosition(float("inf"))
right_motor.setPosition(float("inf"))
left_motor.setVelocity(0.0)
right_motor.setVelocity(0.0)


    
thresh = camera.getWidth() * 0.05 
processed_object_ids = []

gripper_arm.setVelocity(2.0)
gripper_finger_left.setVelocity(2.0)
gripper_finger_right.setVelocity(2.0)

# Helper functions
def move_arm(position):
    """Move the gripper arm to a specific position."""
    gripper_arm.setPosition(position)
    robot.step(TIME_STEP * 10)

def move_fingers(position):
    """Move the gripper fingers to a specific position."""
    gripper_finger_left.setPosition(position)
    gripper_finger_right.setPosition(position)
    robot.step(TIME_STEP * 10)

def move_forwards(speed):
    """Move the robot forwards."""
    left_motor.setVelocity(speed)
    right_motor.setVelocity(speed)

def stop():
    """Stop the robot."""
    left_motor.setVelocity(0.0)
    right_motor.setVelocity(0.0)

def turn(speed):
    """Turn the robot."""
    left_motor.setVelocity(speed)
    right_motor.setVelocity(-speed)
    
def approach_target(target_object, current_state, next_state, targer_color = None):
    position_on_image = target_object.getPositionOnImage()
    relative_position = target_object.getPosition()
    target_object_name =target_object.getModel()
    target_id = target_object.getId()
    print(f'relative pos{relative_position[0]},........{target_object_name}......{target_id }')

    if current_state == "approaching_crate":
      
        if position_on_image[0] < (camera.getWidth() / 2 - thresh):
            turn(-0.2 * MAX_SPEED)
        elif position_on_image[0] > (camera.getWidth() / 2 + thresh):
            turn(0.2 * MAX_SPEED)
        elif relative_position[0] > 0.15:
            move_forwards(0.5 * MAX_SPEED)
      
        else:
            print(f"Approaching the --{target_color} crate...")
            stop()
            return next_state 
        

    elif current_state == "approaching":
        # next_state = None.
        if position_on_image[0] < (camera.getWidth() / 2):
            turn(-0.2 * MAX_SPEED)
        elif position_on_image[0] > (camera.getWidth() / 2):
            turn(0.2 * MAX_SPEED)
        elif relative_position[0] > 0.15:
            move_forwards(0.5 * MAX_SPEED)
        else:
            stop()
            return next_state  

    return None

state = "searching"
target_color = None


#
while robot.step(TIME_STEP) != -1:
    
    objects = camera.getRecognitionObjects()
    if not objects:
        continue
    

    if state == "searching":
        obj_copy = None 
        if objects:
            for obj in objects:
            
                if obj.getId() in processed_object_ids:
                    continue  
                    
                if obj.getModel() == "cylinder": 
                    print(f'presently detected id {obj.getId()}')
                    color_pointer = obj.getColors()
                    
                    color = [color_pointer[i] for i in range(3)]  
            
                    print(f"Detected color: {color}")
                    if color == [1.0, 0.0, 0.0]:
                        target_color = "red"
                    elif color == [0.0, 0.0, 1.0]:  
                        target_color = "blue"
                    elif color == [0.0, 1.0, 0.0]:  
                        target_color = "green"
                    else:
                        continue  

                    print(f"Found {target_color} cylinder. Moving to 'approaching' state.")
                    obj_copy = obj
                    state = "approaching"
                    break
        else:
            turn(0.2 * MAX_SPEED)

    elif state == "approaching":
        
        next_state = approach_target(obj_copy,state, "grabbing")
        if next_state:
            state = next_state
   

    elif state == "grabbing":
        print("Grabbing the object...")
        move_arm(-2.8)  
        robot.step(TIME_STEP * 100)
        move_fingers(0.4)  
        robot.step(TIME_STEP * 100)
        move_arm(0.0)  
       
        state = "searching_for_crate"

   
    elif state == "searching_for_crate":
    
        crate_id = {"red": 745, "blue": 152, "green": 274}
        target_crate = None

        if target_color in crate_id:
            target_id = crate_id[target_color]  
        else:
            print(f"Invalid target color: {target_color}")
    
        object = camera.getRecognitionObjects()
        if len(objects) > 0:
            for obj in object:
            
                if  obj.getModel() == "crate" and obj.getId() == target_id:  
                    print(f"Object ID: {obj.getId()}, Model: {obj.getModel()}")
                    target_crate = obj
                    print(f"Found target crate with ID {target_id} for color {target_color}.")
                    break  
    
        if target_crate:
            print(f"Approaching the {target_color} crate (ID: {target_id})...")
            state = "approaching_crate"  
        else:
         
            turn(0.2 * MAX_SPEED)

        
    elif state == "approaching_crate":  
        print(f"Current state: {state}, Target color: {target_color}, Processed IDs: {processed_object_ids}")
        next_state = approach_target(target_crate, state, "releasing")
        if next_state:
            state = next_state
   
        


    elif state == "releasing":
        print(f"Current state: {state}, Target color: {target_color}, Processed IDs: {processed_object_ids}")

        move_arm(-2.8) 
        robot.step(TIME_STEP * 100)
        move_fingers(0.0)  
        robot.step(TIME_STEP * 200)
        move_arm(0.0)  
        robot.step(TIME_STEP * 50)
        turn(0.2 * MAX_SPEED)
       
        x = obj_copy.getId()
        print(f'id {x}') 
        processed_object_ids.append(x)
        print(f"Object with ID {x} has been processed and will not be searched again.")
     
        state = "searching"  
       