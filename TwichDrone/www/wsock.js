class WSock {
    constructor(url) {
        this.url = url;
        this.websocket = new WebSocket(this.url);    
        
        //his.websocket.onopen = this.onOpen;
        //this.websocket.onclose = this.onClose;
        //this.websocket.onmessage = this.onMessage;
        //this.websocket.onerror = this.onError;

        this.websocket.addEventListener('open', this.onOpen);
        this.websocket.addEventListener('close', this.onClose);
        this.websocket.addEventListener('message', this.onMessage);
        this.websocket.addEventListener('error', this.onError);
  
    }

    // handlers
    
    onOpen(evt) {
        DEBUG("Connected to Drone");
    }
      
    onClose(evt) {
        DEBUG("Disconnected from Drone");
    }
  
    onMessage(evt) {
        DEBUG(evt.data + '\n');
        
        /*
        try {
            var a = evt.data;
        } catch (e) {
            DEBUG('This doesn\'t look like a valid JSON: ', evt.data);
            return;
        }
        */
    
        //var msg = String.fromCharCode(null,evt.data);
        //DEBUG("response: " + evt + '\n');
        //var dataView = new DataView(evt);
        //var decoder = new TextDecoder('utf-8');
        //var decodedString = decoder.decode(dataView);
        //DEBUG("response: " + evt + '\n');
        
    }

    onError(evt) {
        DEBUG('error: ' + evt.data + '\n');
        //this.websocket.close();
          
    }

    // functions

    Send(message) {
        //DEBUG("sent: " + message + '\n'); 
        this.websocket.send(message);
    }

    Disconnect() {
        this.websocket.close();
    }

}


