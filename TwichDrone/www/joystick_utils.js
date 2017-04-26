// nipplejs (js)

function CreateJoystick(wsock) {
	var joystick = nipplejs.create({
	  zone: document.getElementById('joystick_control'),
	  mode: 'static',
	  position: {right: '130', top: '10'},
	  color: 'red',
	  size: 150,
	  restOpacity: 0.8
	});
	//debug_joystick(joystick);
	if (wsock != null) {
	   WSNotify(joystick, wsock);
	}
	return joystick;
}

function WSNotify(joystick, wsock) {

  var JData = Object();
    
  JData.distance = 0;
  JData.angle = 0;
  JData.x = "";
  JData.y = "";
  JData.kind = "joystick";
  moved = false;
  
  DEBUG_CLEAN();

  joystick.on('start end move plain:up plain:down plain:left plain:right', function(evt, data) {
    if (evt.type == 'move' && data != null) {
      JData.distance = data.distance;
      JData.angle    = data.angle.radian;
      moved = true;
    }
    if (evt.type == 'plain:up')    { JData.y = 'up';    moved = true; }
    if (evt.type == 'plain:down')  { JData.y = 'down';  moved = true; }
    if (evt.type == 'plain:left')  { JData.x = 'left';  moved = true; }
    if (evt.type == 'plain:right') { JData.x = 'right'; moved = true; }

    if (moved) {
        var msg = JSON.stringify(JData);
    	wsock.Send(msg);
    }
    
    if (evt.type == 'end') {
      //DEBUG('Event: '+ evt.type + ' Data: ' + data + '<br/>');
      JData.distance = 0;
      JData.angle = 0;
      JData.x = 0;
      JData.y = 0;
      JData.kind = "joystick";
      var msg = JSON.stringify(JData);
      wsock.Send(msg);
    }    
  });
}




function debug_joystick(joystick) {

  var distance = 0;
  var angle = 0;
  var moved = false;
  var x = "";
  var y = "";

  DEBUG_CLEAN();

  joystick.on('start end move plain:up plain:down plain:left plain:right', function(evt, data) {
    if (evt.type == 'start' || evt.type == 'end') {
      DEBUG('Event: '+ evt.type + ' Data: ' + data + '<br/>');
    }
    if (evt.type == 'move' && data != null) {
      distance = data.distance;
      angle    = data.angle.degree;
      moved = true;
      
    }
    if (evt.type == 'plain:up')    { y = 'up';    moved = true; }
    if (evt.type == 'plain:down')  { y = 'down';  moved = true; }
    if (evt.type == 'plain:left')  { x = 'left';  moved = true; }
    if (evt.type == 'plain:right') { x = 'right'; moved = true; }

    if (moved) {
      DEBUG_ADD("Distance: " + distance + " " 
                   + "Angle: " + angle + " "
                   + "X: " + x + " "
                   + "Y: " + y + "<br/>");
    }
  });
}
