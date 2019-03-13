$(document).ready(function(){
    $.get("/api/v1.0/house/myhouse", function(data){
        if ("4102" == data.errcode) {
            location.href = "/login.html";
        } else if ("4101" == data.errcode) {

                $(".auth-warn").show();
                return;
            } else if (data.errcode == "0") {
            $("#houses-list").html(template("houses-list-tmpl", {houses: data.data.houses}));
        };

    });
})