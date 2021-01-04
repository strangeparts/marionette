let token = '';
let tuid = '';

const twitch = window.Twitch.ext;

twitch.onContext(function (context) {
  twitch.rig.log(context);
});

twitch.onAuthorized(function (auth) {
  // save our credentials
  token = auth.token;
  tuid = auth.userId;

  // enable the button
  $('#cycle').removeAttr('disabled');

  $.ajax(requests.get);
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

$(function () {
  attach_onclick('l');
  attach_onclick('r');
  attach_onclick('f');
  attach_onclick('b');
  attach_onclick('tl');
  attach_onclick('tr');
});
