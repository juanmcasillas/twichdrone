function DEBUG(msg) {
	var D = document.getElementById("debug");
	D.innerHTML = msg;
}
function DEBUG_CLEAN() {
	var D = document.getElementById("debug");
	D.innerHTML = '';
}
function DEBUG_ADD(msg) {
	var D = document.getElementById("debug");
	D.innerHTML += msg;
}