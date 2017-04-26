import time

import thread
import threading
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import model

class WSockHandler(WebSocket):
    
    def handleMessage(self):
        
        # can't send messages TO client. I don't know why. Try at home.
        try:
            model.MODEL.HandleData(self.data, self)
            #model.MODEL.printdata()
            #on windows (work) this crashes
            #self.sendMessage(unicode("TwichDrone ready to rock!","utf-8"));
            
        except Exception, e:
            print "Exception: ",e

    def handleConnected(self):
        s = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print "[WEBSOCKET][%s][%s:%d] Connected" % (s, self.address[0], self.address[1])
        

    def handleClose(self):
        s = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print "[WEBSOCKET][%s][%s:%d] Closed" % (s, self.address[0], self.address[1])




        
def websocketserver_thread(host='',port=8000):
    server = SimpleWebSocketServer(host, port, WSockHandler)
    server.serveforever()
    
def websocketserver_start(host='',port=8000):
     thread.start_new_thread(websocketserver_thread , (host, port ))
     

if __name__ == "__main__":
    
    websocketserver_thread()
