jQuery(document).ready(function(){

    function updateCountyList() {
        $.ajax({
            type: "POST",
            url: "/select_county",
            data: {
                district: $("#district").val()
            },
            success: function(data) {
                $("#county").html(data);
                var firstCounty = $("#county option:first").val();
                $("#county").css("width", firstCounty.length + 5 + "ch");
                updateParishList();
            }
        });
    }

    function updateParishList() {
        $.ajax({
            type: "POST",
            url: "/select_parish",
            data: {
                county: $("#county").val()
            },
            success: function(data) {
                $("#parish").html(data);
                var firstParish = $("#parish option:first").val();
                $("#parish").css("width", firstParish.length + 5 + "ch");
            }
        });
    }

    function changePrice(e) {
        e.preventDefault();
        $.ajax({
            type: "POST",
            url: "/predict",
            data: {
                district: $("#district").val(),
                county: $("#county").val(),
                parish: $("#parish").val(),
                built_area: $("#built_area").val(),
                rooms: $("#rooms").val(),
                bathrooms: $("#bathrooms").val(),
                fitted_wardrobes: $("#fitted_wardrobes").is(":checked"),
                air_conditioning: $("#air_conditioning").is(":checked"),
                terrace: $("#terrace").is(":checked"),
                balcony: $("#balcony").is(":checked"),
                storeroom: $("#storeroom").is(":checked"),
                with_lift: $("#with_lift").is(":checked"),
                swimming_pool: $("#swimming_pool").is(":checked"),
                garden: $("#garden").is(":checked"),
                green_area: $("#green_area").is(":checked"),
                is_apartment: $(".slick-current").children("img").attr("value") == "Apartment",
            },
            success: function(data) {
                var prediction = data.prediction;
                $(".price").text(prediction);

                var error_range = data.rmse_low + " - " + data.rmse_high;
                $(".price").attr("aria-label", error_range);
                
                if (data.hasOwnProperty("error")) {
                    alert("Não temos informação para '" + data.error + "'.");
                }
            }
        });
    }

    function resizeInput() {
        this.style.width = this.value.length + 3 + "ch";
    }

    function resizeSelect() {
        var text = $(this).children("option:selected").text();
        this.style.width = text.length + 3 + "ch";
    }

    $("#district").change(function() {
        updateCountyList();
    });

    $("#county").change(function() {
        updateParishList();
    });

    $("#data-form").submit(function(e) {
        changePrice(e);
    });

    var input = document.querySelectorAll('input[type="number"]');
    input.forEach(function(element) {
        element.addEventListener('input', resizeInput); 
        resizeInput.call(element); 
    });

    var select = document.querySelectorAll('select');
    select.forEach(function(element) {
        element.addEventListener('input', resizeSelect); 
        resizeSelect.call(element); 
    });

    var input_rooms = document.querySelector('#rooms');
    input_rooms.addEventListener('change', function() {
        var rooms = parseInt(input_rooms.value);
        var label_rooms = document.querySelector('#label-rooms');
        if (rooms > 1) {
            label_rooms.textContent = "divisões";
        }else{
            label_rooms.textContent = "divisão";
        }
    });

    var input_bathrooms = document.querySelector('#bathrooms');
    input_bathrooms.addEventListener('change', function() {
        var bathrooms = parseInt(input_bathrooms.value);
        var label_bathroom = document.querySelector('#label-bathrooms');
        if (bathrooms > 1) {
            label_bathroom.textContent = "WCs";
        }else{
            label_bathroom.textContent = "WC";
        }
    });

    $('.carousel-selector').slick({
        slidesToShow: 1,
    });

    updateCountyList();
});