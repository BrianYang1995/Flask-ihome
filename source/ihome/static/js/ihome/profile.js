function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function () {
    $.get("/api/v1.0/profile", function(data){
        if ("4102" == data.errcode) {
            location.href = "/login.html";
        }
        else if ("0" == data.errcode) {
            $("#user-name").val(data.data.name);
            if (data.data.avatar) {
                $("#user-avatar").attr("src", data.data.avatar);
            }
        }
    })
    $("#form-avatar").submit(function (e) {
        // 组织浏览器对于表单的默认行为
        e.preventDefault();
        $('.image_uploading').fadeIn('fast');
        var options = {
            url: "/api/v1.0/avatar",
            method: "post",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (data) {
                if (data.errcode == "0") {
                    $('.image_uploading').fadeOut('fast');
     console.log(data.data);
                    $("#user-avatar").attr("src", data.data);
                } else if ("4102" == data.errcode) {
                    location.href = "/login.html";
                } else {
                    console.log(data.errmsg);
                }
            }
        };
        $(this).ajaxSubmit(options);
    })
    $("#form-name").submit(function(e){
        e.preventDefault();
        username = $("#user-name").val()
        var data = {name: username};
        var jsonData = JSON.stringify(data);
        $.ajax({
            url:"/api/v1.0/name",
            type:"PUT",
            data: jsonData,
            contentType: "application/json",
            dataType: "json",
            headers:{
                "X-CSRFTOKEN":getCookie("csrf_token"),
            },
            success: function (data) {
                if (data.errcode == '0') {
                    $(".error-msg").hide();
                    showSuccessMsg(); // 展示保存成功的页面效果
                } else if ("4001" == data.errcode) {
                    $(".error-msg").show();
                } else if ("4101" == data.errcode) { // 4101代表用户未登录，强制跳转到登录页面
                    location.href = "/login.html";
                }
            }
        });
    })
})

