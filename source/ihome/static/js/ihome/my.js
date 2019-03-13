function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function logout() {
    $.ajax({
        url: "/api/v1.0/session",
        method: 'DELETE',
        dataType: 'json',
        headers: {
            'X-CSRFToken': getCookie('csrf_token')
        },
        success: function (data) {
            if (data.errcode == '0') {
            location.href = "/";
        }
        }
    })
}


$(document).ready(function(){
    $.get("/api/v1.0/my", function(data) {
        if ("4102" == data.errcode) {
            location.href = "/login.html";
        }
        else if (data.errcode == '0') {
            $("#user-name").html(data.data.name);
            $("#user-mobile").html(data.data.mobile);
            if (data.data.avatar) {
                $("#user-avatar").attr("src", data.data.avatar);
            }
            if(data.data.is_auth == 1) {
                $('<li><div class=\"menu-title menu-radius\"><a href=\"/newhouse.html\"><h3>发布房源</h3></a><div></li>').insertAfter($('.menus-list li').eq(3)
)

            }
        }
    }, "json");
})