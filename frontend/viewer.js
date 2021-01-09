let token = '';
let tuid = '';

const twitch = window.Twitch.ext;
const buttons = ['l', 'r', 'f', 'b', 'tl', 'tr', 'CAMDOWN', 'CAMRESET', 'CAMUP'];

twitch.onContext(function (context) {
  twitch.rig.log(context);
});

twitch.onAuthorized(function (auth) {
  twitch.rig.log("onAuthorized");

  // save our credentials
  token = auth.token;
  tuid = auth.userId;

  enable_buttons();
});

function logError(_, error, status) {
  twitch.rig.log('EBS request returned '+status+' ('+error+')');
}

function logSuccess(hex, status) {
  twitch.rig.log('EBS request returned '+hex+' ('+status+')');
}

function createRequest (type, command) {
  twitch.rig.log('createRequest(' + type + ", " + command + ")");
  return {
    type: type,
    url: location.protocol + '//localhost:8000/command?command=' + command,
    headers: { 'Authorization': 'Bearer ' + token },
    success: logSuccess,
    error: logError
  };
}

function attach_onclick(button_id) {
  $('#' + button_id).click(function () {
    if(!token) { return twitch.rig.log('Not authorized'); }
    twitch.rig.log('Button ' + button_id + ' pressed');
    $.ajax(createRequest('GET', button_id));
  });
}

function enable_buttons() {
  $(function () {
    $.each(buttons, function(i, val) {
      twitch.rig.log("Enabling button #" + val);
      $('#' + val).removeClass('disabled');
    });
  });
}

$(function () {
  $.each(buttons, function(i, val) {
    attach_onclick(val);
  });
});
