import serial
import time
import json
import subprocess
import sys
import argparse

class CreateAction:
    def __init__(self, startCalibration: bool):
        self.isCalibrationDone = not startCalibration
        self.hasWhiteKingMoved = False
        self.hasBlackKingMoved = False
        self.reset()
        
    def reset(self):
        self.data = [] #A list of tuples. First element is piece. Second element is coordinate
        self.isCastling = False #'True' if in the process of castling
        self.actionType = ''
        self.actionResult = ''
        self.move = ''
        self.isCalibrationDone = self.isCalibrationDone
        
    def to_dict(self):
        return {
            'move': self.move,
            'isCastling': self.isCastling,
            'actionType': self.actionType,
            'actionResult': self.actionResult,
            'isCalibrationDone': self.isCalibrationDone
        }

    def isMoveDone(self):
        pieces = dict()
        coordinates = set()
        for piece, coordinate in self.data:
            #if coordinate == "e1" and (g1 or h1 or f1 or a1 or c1 or d1) (WHITE)
            #if hasKingMoved == False and 
            #KING MOVED LOGIC
            #if coordinate == "e8" or "e1"
            if piece in pieces:
                if((self.hasWhiteKingMoved == False and ((coordinate == "e1" and ("h1" in coordinates or "a1" in coordinates)) or ((coordinate == "a1" or coordinate == "h1") and ("e1" in coordinates)))) or
                  (self.hasBlackKingMoved == False and((coordinate == "e8" and ("h8" in coordinates or "a8" in coordinates)) or(( coordinate == "a8" or coordinate == "h8") and ("e8" in coordinates))))) :
                    self.isCastling = True
                # if (not self.isCastling) and ((piece == "K" and "R" in pieces or piece == "k" and "r" in pieces) or \
                    # (piece == "R" and "K" in pieces and piece == "r" and "k" in pieces)):
                    # Castling
                    # self.isCastling = True
                elif((self.isCastling) and len(self.data) == 4):
                    self.isCastling = False
                    
                    self.actionType = "Castling"
                    if("a1" in coordinates):
                        self.move = "Pe1c1"
                        self.hasWhiteKingMoved = True
                    elif("a8" in coordinates):
                        self.hasBlackKingMoved = True
                        self.move = "pe8c8"
                    elif("h8" in coordinates):
                        self.move = "pe8g8"
                        self.hasBlackKingMoved = True
                    else:
                        self.move = "Pe1g1"
                        self.hasWhiteKingMoved = True
                    #self.move = resPiece + coorInfo[-1]
                    #self.actionResult = currPiece + currCoor
                # elif (self.isCastling) and ((piece == "K" and "K" in pieces and pieces["K"][0] == 1 and "R" in pieces and pieces["R"][0] == 2) or \
                      # (piece == "k" and "k" in pieces and pieces["k"][0] == 1 and "r" in pieces and pieces["r"][0] == 2) or \
                      # (piece == "R" and "R" in pieces and pieces["R"][0] == 1 and "k" in pieces and pieces["k"][0] == 2) or \
                      # (piece == "r" and "r" in pieces and pieces["r"][0] == 1 and "k" in pieces and pieces["k"][0] == 2)):
                    # #castling complete
                    # self.actionType = "Castling"
                    # currPiece, currCoor = piece, pieces[piece][1]+coordinate
                    # pieces.pop(piece)
                    # resPiece, coorInfo = next(iter(pieces.items()))
                    # self.move = resPiece + coorInfo[-1]
                    # self.actionResult = currPiece + currCoor
                    break
                elif(not self.isCastling and len(self.data) == 3):
                    self.actionType = "Capture"
                    self.move = piece + pieces.pop(piece)[1] + coordinate
                    resPiece, coor_info = next(iter(pieces.items()))
                    if(self.move.startswith("Pe1")):
                        self.hasWhiteKingMoved = True
                    elif(self.move.startswith("pe8")):
                        self.hasBlackKingMoved = True
                    self.actionResult = resPiece + coor_info[1]
                    break
                elif(not self.isCastling and len(self.data) == 2):
                    self.actionType = "Move"
                    self.move = piece + pieces.pop(piece)[1] + coordinate
                    if(self.move.startswith("Pe1")):
                        self.hasWhiteKingMoved = True
                    elif(self.move.startswith("pe8")):
                        self.hasBlackKingMoved = True
                    self.actionResult = ''
                    break
                
                pieces[piece] = (pieces[piece][0] + 1, pieces[piece][1] + coordinate)
                coordinates.add(coordinate)
            else: 
                pieces[piece] = (1, coordinate)
                coordinates.add(coordinate)
        # print(pieces, coordinates, self.isCastling)
        if(self.actionType != ''):
            return True
        else:
            return False
            
    def Send_Action(self):
        ndjson_data = ""
        for key, value in self.to_dict().items():
            ndjson_data += json.dumps({key: value}) + "\n"
        sys.stdout.flush()
        #TODO: Reset after sending data to ensure all fuields go back to null?
        self.reset()
        print(ndjson_data)



class Arduino:
    def __init__(self):
        # self.arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600)
        self.arduino = serial.Serial()
        self.pieces = set({"P", "R", "N", "B", "Q", "K",
                           "p", "r", "n", "b", "q", "k"})
         

    def establishSerialCommunication(self, startCalibration, beginGame):
        action = CreateAction(startCalibration)
        # print("Entered")
        while True:
            # data_decoded = ""
            # if(startCalibration):
            #     action.isCalibrationDone = False
            #     # print(self.arduino.in_waiting)
            #     while self.arduino.in_waiting == 0:
            #         self.arduino.write("Start Calibration".encode('utf-8'))
            #         time.sleep(2.5)
            # if(beginGame):
            #     beginGame = False
            #     while self.arduino.in_waiting == 0:
            #         self.arduino.write("Begin Game".encode('utf-8'))
            #         time.sleep(2.5)
            # if (self.arduino.in_waiting > 0):
            #     data_decoded = self.arduino.readline().decode().rstrip()
            #     #print(data_decoded)
            # # data_decoded = input("Enter info: ")
            data_decoded = input("Enter your move")
            if (data_decoded != "" and data_decoded.startswith('Calibration Complete')):
                # print(data_decoded)
                action.actionResult = data_decoded.split(":")[-1] # Send min and max voltage as a space divided string
                action.isCalibrationDone = True
                startCalibration = False
                action.Send_Action()
                # while self.arduino.in_waiting == 0:
                    # self.arduino.write("Wait for Begin Game".encode('utf-8'))
                    # time.sleep(2.5)
            elif(data_decoded != "" and data_decoded.startswith('Begin Game')):
                # print(data_decoded)
                action.actionType = "Begin Game"
                action.isCalibrationDone = True
                action.Send_Action()
            elif(data_decoded != "" and self.Validate_Data(data_decoded)):
                #print(data_decoded)
                piece, coordinate = data_decoded[0], data_decoded[1:]
                #print(piece+"$"+coordinate)
                if((piece, coordinate) in action.data): #Piece is lifted and placed down
                    action.data.remove((piece, coordinate))
                else:
                    action.data.append((piece, coordinate))
                
                if(action.isMoveDone()):
                    # send action info over to JS script
                    action.Send_Action()
                    pass
                
                    
            else:
                pass
                # message = f"Error in data received from arduino. Data received was {data_decoded}"
                # subprocess.Popen(['python3', 'logger.py', '-text', message, "-filename", "error.log"])
            sys.stdout.flush()
        return
    
    def Validate_Data(self, data_decoded):
        '''
        Data from Arduino Uno has to be of the format "<piece type><column coordinate (letter)><row coordinate (number)
        '''
        try:
            if(len(data_decoded) != 3):
                message = f"Data should be of ther form <piece><coordinate>. Data received was {data_decoded}"
                subprocess.Popen(['python3', 'logger.py', '-text', message, "-filename", "error.log"])
                return False
            if(data_decoded[0] not in self.pieces):
                message = f"First character is not a valid piece. Data received was {data_decoded}"
                subprocess.Popen(['python3', 'logger.py', '-text', message, "-filename", "error.log"])
                return False
            if(not data_decoded[1].isalpha()):
                message = f"Second character must be a letter for the column coordinate. Data received was {data_decoded}"
                subprocess.Popen(['python3', 'logger.py', '-text', message, "-filename", "error.log"])
                return False
            if(not data_decoded[2].isnumeric()):
                message = f"Third character must be a number for the row coordinate. Data received was {data_decoded}"
                subprocess.Popen(['python3', 'logger.py', '-text', message, "-filename", "error.log"])
                return False
            return True
        except Exception as e:
            #Data was not decoded properly, or is not a string after decoding
            subprocess.Popen(['python3', 'logger.py', '-text', str(e), "-filename", "error.log"])
            return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Serial module to establish communication with arduino')
    parser.add_argument('-startCalibration', metavar='C', type=bool, nargs='?', required=False, default=False,
                        help='Calibrate the board')
    parser.add_argument('-beginGame', metavar='C', type=bool, nargs='?', required=False, default=False,
                        help='Write begin game')
    args = parser.parse_args()
    startCalibration = args.startCalibration
    beginGame = args.beginGame
    
    arduino = Arduino()
    time.sleep(0.1)
    sys.stdout.flush()
    arduino.establishSerialCommunication(startCalibration, beginGame)

    # if arduino.arduino.isOpen():
    #     #Get data and validate it
    #     arduino.establishSerialCommunication(startCalibration, beginGame)
        
