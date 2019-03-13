function hrefBack() {
    history.go(-1);
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function decodeQuery(){
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function(result, item){
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

function showErrorMsg(msg) {
    $(".popup>p").html(msg);
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function(){
            $('.popup_con').fadeOut('fast',function(){}); 
        },1000) 
    });
}

$(document).ready(function(){
    $.get("/api/v1.0/check_login", function(data) {
        if ("0" != data.errcode) {
            location.href = "/login.html";
        }
    }, "json");
    $(".input-daterange").datepicker({
        format: "yyyy-mm-dd",
        startDate: "today",
        language: "zh-CN",
        autoclose: true
    });
    $(".input-daterange").on("changeDate", function(){
        var startDate = $("#start-date").val();
        var endDate = $("#end-date").val();

        if (startDate && endDate && startDate > endDate) {
            showErrorMsg("日期有误，请重新选择！");
        } else {
            var sd = new Date(startDate);
            var ed = new Date(endDate);
            days = (ed - sd)/(1000*3600*24) + 1;
            var price = $(".house-text>p>span").html();
            var amount = days * parseFloat(price);
            $(".order-amount>span").html(amount.toFixed(2) + "(共"+ days +"晚)");
        }
    });

    var house_id = decodeQuery()["hid"];
    $.get("/api/v1.0/house/detail?house_id="+house_id, function (data) {
        if (data.errcode = "0") {
            $(".house-info>img").attr("src", data.data.images[0].url);
            $(".house-text>h3").html(data.data.house_info.title);
            $(".house-text>p>span").html((data.data.house_info.price/100.0).toFixed(0));
        }
    });
    $(".submit-btn").on("click", function(e) {
        if ($(".order-amount>span").html()) {
            $(this).prop("disabled", true);
            var startDate = $("#start-date").val();
            var endDate = $("#end-date").val();
            var data = {
                "house_id":house_id,
                "start_date":startDate,
                "end_date":endDate
            };
            $.ajax({
                url:"/api/v1.0/order",
                type:"POST",
                data: JSON.stringify(data), 
                contentType: "application/json",
                dataType: "json",
                headers:{
                    "X-CSRFTOKEN":getCookie("csrf_token"),
                },
                success: function (data) {
                    if ("4102" == data.errcode) {
                        location.href = "/login.html";
                    } else if ("4103" == data.errcode) {
                        showErrorMsg("房间已被抢定，请重新选择日期！"); 
                    } else if ("0" == data.errcode) {
                        location.href = "/orders.html";
                    }
                }
            });
        }
    });
})
