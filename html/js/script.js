$(function() {
	get_notifications();
	$('.ajax_link').on('click', function(e){return ajax_link(this);});

	$('body')
		.on('mouseenter', 'a.actor', function(e){
			var match = $(this).attr('class').match(/actor_id_(\d+)/i)
			if(match){
				var id = match[1]
				$('body').append('<div class="actor_image_container"><img id="actor_image_{0}" class="actor_image" src="{1}actor_image/{0}" /></div>'.format(id, _base));
			}			
		})
		.on('mouseleave', 'a.actor', function(e){
			var match = $(this).attr('class').match(/actor_id_(\d+)/i)
			if(match){
				var id = match[1]
				$('#actor_image_{0}'.format(id)).parent().remove();
			}
		})
		.on('mousemove', 'a.actor', function(e){
			var match = $(this).attr('class').match(/actor_id_(\d+)/i)
			if(match){
				var id = match[1]
				$('#actor_image_{0}'.format(id)).parent()
					.css("top", e.clientY-60).css("left", e.clientX+10)
			}
		})
		.on("contextmenu", function(e){
			$("#contextMenu").remove()
		})		
		.on("contextmenu", 'a.actor', function(e){
			var match = $(this).attr('class').match(/actor_id_(\d+)/i)
			if(match){
				var id = match[1];
				var contextmenuitems =
				[
					contextmenuitemTemplate.format(contextlinkTemplate.format("Details",_base+"model/"+id)),
					contextmenuitemTemplate.format(contextlinkTemplate.format("Videos",	_base+"videos?mid="+id)),
					contextmenuitemTemplate.format(contextlinkTemplate.format("Nzbs",	_base+"nzbs?mid="+id))
				];

				var contextmenu = contextmenuTemplate.format(contextmenuitems.join(""));
				contextmenu = $(contextmenu).css({
					display: "block",
					left: e.pageX,
					top: e.clientY-60
				  }).appendTo("body");		
				  return false;		
			}			
		});
});

var contextmenuTemplate = ' <div id="contextMenu" class="dropdown clearfix"><ul class="dropdown-menu" role="menu" aria-labelledby="dropdownMenu" style="display:block;position:static;margin-bottom:5px;">{0}</ul></div>';
var contextmenuitemTemplate = '<li>{0}</li>';
var contextlinkTemplate = '<a href="{1}">{0}</a>';


function ajax_link(sender){
	$.get(
		$(sender).attr("href")
	)
	.success(function (data) {
		if(data != "ok"){
			console.log("error");
			console.log($(sender).attr("href"));
		}
	})
	.fail(function(){
		console.log($(sender).attr("href"));
	});

	return false;
}

function ajax_form(e, callback, error){
	var sender = $(e.target);
	var form = sender.closest("form");

	var data = form.serializeArray();

	form.find("input").prop( "disabled", true );

	if (sender.is("input[type='submit']")){
		data.push({ name: sender.attr("name"), value: sender.attr("value") });
	}

	$.ajax({
		type: 'POST',
		url: form.attr("action"),
		data: data,
		success: function(data){
			form.find("input").prop( "disabled", false );
			if(callback)
				callback(data)
		},
		error: error
	 });

	return false;
}

function isScrolledIntoView(elem)
{
    var $elem = $(elem);
    var $window = $(window);

    var docViewTop = $window.scrollTop();
    var docViewBottom = docViewTop + $window.height();

    var elemTop = $elem.offset().top;
    var elemBottom = elemTop + $elem.height();

    return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
}

if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

function timeSince(date){
    var seconds = Math.floor((new Date() - date) / 1000);
	var output = '';

    var interval = Math.floor(seconds / 86400);
    if (interval >= 1) {
        output += interval + "d";
		seconds -= 86400 * interval;
    }
    interval = Math.floor(seconds / 3600);
    if (interval >= 1) {
        output += interval + "h";
    }
    return output || "New";
}

function formatTime(seconds) {
	var value = "";
	if (seconds < 0)
		value = "-";
	seconds = Math.floor(Math.abs(seconds));

	var minute = 60;
	var hour = 60 * minute;

	var hours = Math.floor(seconds / hour);
	seconds -= hours * hour;
	var minutes = Math.floor(seconds / minute);
	;
	seconds -= minutes * minute;

	if (hours > 0) {
		value = value + String(hours) + ":"
		if (minutes <= 9)
			value = value + '0';
	}
	if (hours > 0 || minutes > 0) {
		value = value + String(minutes) + ":"
		if (seconds <= 9)
			value = value + '0';
	}

	value += String(seconds)

	return value;
}

function pointerEventToXY(e){
      var out = {x:0, y:0};
      if(e.type == 'touchstart' || e.type == 'touchmove' || e.type == 'touchend' || e.type == 'touchcancel'){
        var touch = e.originalEvent.touches[0] || e.originalEvent.changedTouches[0];
        out.x = touch.pageX;
        out.y = touch.pageY;
      } else if (e.type == 'mousedown' || e.type == 'mouseup' || e.type == 'mousemove' || e.type == 'mouseover'|| e.type=='mouseout' || e.type=='mouseenter' || e.type=='mouseleave') {
        out.x = e.pageX;
        out.y = e.pageY;
      }
      return out;
    }

function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

var cur_seed = 0;
function get_nzbs(page, count, q, all, aid, callback, seed){
	if (seed !== cur_seed){
		seed = Math.random();
		cur_seed = seed;
		page = 1;
		$("#nzbs .nzbs").remove()
	}
	$.get(
		_base + "json/nzbs",
		{
			"p": page,
			"c": count,
			"q": q,
			"all": all,
			"mid": aid,
			"seed": seed
		}
	).success(function(data){
		if (seed == data.seed)
			if (callback)
				callback(data, function(){ get_nzbs(++page, count, q, all, aid, callback, parseFloat(data.seed)); });
	});
}

function get_notifications(){
	if($("#notifications").length == 0) return;
	
	$.get(
		_base + "json/notifications",
		$.cookie("note", JSON.parse)
	)
	.success(function (data) {
		if (data["notes"]) {
			console.log(data["notes"]);
			for (var i = 0; i < data.notes.length; i++){
				$("#notifications").append(
					$("<div>"+data.notes[i]+"</div>")
						.delay(3000*($("#notifications")
								.children().length+1)).fadeOut(1000, function () {
									$(this).remove();
								})
				);
			}
			delete data["notes"];
		}
		if (data["searches"]){
			for (var i = 0; i < data.searches.length; i++){
				$.onSearchComplete(data.searches[i].query);
			}
			delete data["searches"];
		}
		$.cookie("note", JSON.stringify(data));
		$.onNotification(data);
	})
	.fail(function(){
		console.log("failed");
	})
	.always(function(){
		setTimeout(get_notifications, 2000);;
	});
}

var on_notification_subs = [];
function on_notification(data){
	for(var i = 0; i < on_notification_subs.length; i++){
		on_notification_subs[i](data)
	}
}

function isFunction(functionToCheck) {
 var getType = {};
 return functionToCheck && getType.toString.call(functionToCheck) === '[object Function]';
}
var onSearchCompleteCallbacks = [];

$.onSearchComplete = function(query){
	for(var i = 0; i < onSearchCompleteCallbacks.length; i++){
		onSearchCompleteCallbacks[i](query);
	}
};
$.searchComplete = function(callback){
	if (isFunction(callback))
		onSearchCompleteCallbacks.push(callback);
};
var onNotificationCallbacks = [];

$.onNotification = function(query){
	for(var i = 0; i < onNotificationCallbacks.length; i++){
		onNotificationCallbacks[i](query);
	}
};
$.notification = function(callback){
	if (isFunction(callback))
		onNotificationCallbacks.push(callback);
};