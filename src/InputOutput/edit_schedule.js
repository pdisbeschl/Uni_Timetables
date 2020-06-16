//Load the json schedule from the schedule_info.js file
//Dictionary about the schedule that was generated
var schedule_json = schedule;
//Hard constraints of the schedule
var input_data = input_raw;
//The current programmes that we have and consider (Can be made generic)
var programmes = ['BAY1','BAY2','BAY3','MAAIY1','MADSDMY1'];
//Colour of the courses
var course_colours = ['#FFB5E8', '#B28DFF', '#DCD3FF', '#AFF8D8', '#BFFCC6', '#FFC9DE', '#FF9CEE', '#C5A3FF', '#A79Aff', '#C4FAF8',
               '#DBFFD6', '#FFABAB', '#FFCCF9', '#D5AAFF', '#B5B9FF', '#85E3FF', '#F3FFE3', '#FFBEBC', '#FCC2FF', '#ECD4FF',
               '#97A2FF', '#ACE7FF', '#E7FFAC', '#FFCBC1', '#F6A6FF', '#FBE4FF', '#AFCBFF', '#6EB5FF', '#FFFFD1', '#FFF5BA'];
//A dictionary which maps a course to the used colour
var colour_palette = {"":"#FFFFFF"};
var selected = false;
var selected_course;

//Wait until the html is loaded and fully generated
window.addEventListener('load', function () {
    //Add a download button to the page which allows to export the (modified) schedule in json format
    //var btn = document.createElement("BUTTON");
    //btn.innerHTML = "Download";
    //btn.onclick = function () { download("schedule_info.js",JSON.stringify(schedule_json)); };
    //document.body.appendChild(btn);
    $("#download").click(function() { download("schedule_info.js",JSON.stringify(schedule_json));});

    //Initialise click events for all table entries that they respond to clicks (
    for (var year in programmes) {
        var table = document.getElementById(programmes[year]);
        if (table != null) {
            for (var i = 0; i < table.rows.length; i++) {
                for (var j = 0; j < table.rows[i].cells.length; j++)
                    table.rows[i].cells[j].addEventListener("click", function() { getCourseInfo(this);});
                }
            }
    }

    //Assigns each course a colour
    loadColourPalette();
    //Colours all the courses in the respective colour
    colourCourses();
})

function swap_courses(course) {

}

/**
Upon clicking on a cell highlight the cell and show the information about the course
**/
function getCourseInfo(cell) {
    document.getElementById("myNav").style.height = "0%";
    colourCourses();

    //Get the course id - If we clicked on a room cell we just redirect to the course cell
    course_cell_id = cell.id.replace('room','course');
    course_cell = document.getElementById(course_cell_id);
    cid = course_cell.textContent;
    cid = cid.replace(/\s/g,'');

    //Get the timeslot that was clicked
    timeslot = cell.classList[0];
    timeslot = timeslot.replace('_',' ');
    let course;

    //Query the courses scheduled on that timeslot in the schedule.json and get the data
    if (schedule_json[timeslot] !== undefined) {
        schedule_json[timeslot].forEach( (course_info, index) => {
            if(cid == course_info['CourseID']) {
                console.log(course_info);
        	    course = course_info;
            }
        })
    }
    //If we could not find a course or if we already selected one then we don't want to do anything
    if (course === undefined || selected_course) {
        //return
    }

    //If we clicked on the room we still want to colour the course and room cell of the clicked cell
    cells = document.getElementsByClassName(cell.classList[1]);
    for (var i = 0; i < cells.length; i++) {
        cells[i].style.backgroundColor= shadeColor(colour_palette[cid],-40);
    }

    //Show the overlay with the course information
    overlay = document.getElementById("CourseInfoOverlay")
    overlay.innerHTML = "";
    $('#myNav').css('background-color', colour_palette[cid]);
    for(c in course) {
        para = document.createElement("p");
        para.style.width = "75%";
        info_entry = document.createTextNode(c + ': ' + course[c]);
        para.appendChild(info_entry);
        overlay.appendChild(para);
    }


    setTimeout(function(){
        document.getElementById("myNav").style.height = "25%"
        $('.EE').remove();
        rand = Math.floor(Math.random() * 16)
        if (rand == 0)
            img = $('#myNav').prepend('<img class="EE" src="https://i.imgur.com/ZZ7YDFU.jpg" onerror="this.style.display=\'none\'">')
        else if (rand == 1)
            img = $('#myNav').prepend('<img class="EE" src="https://i.imgur.com/L4FkiF2.jpg" onerror="this.style.display=\'none\'">')
        else if (rand == 2)
            img = $('#myNav').prepend('<img class="EE" src="https://i.imgur.com/kvxxZV3.jpg" onerror="this.style.display=\'none\'">')
        else if (rand == 3)
            img = $('#myNav').prepend('<img class="EE" src="https://i.imgur.com/18aZSAB.jpg" onerror="this.style.display=\'none\'">')
    }, 200);

    //selected_course = true;

    return course;
}

/*
Fills the colour_palette dictionary with a <course,colour> for every course
*/
function loadColourPalette() {
    course_ids = Object.keys(input_data.CourseData);
    for (let [index, course_key] of course_ids.entries()) {
        colour_palette[course_key] = course_colours[index];
    }
}

/*
Iterate over all cells that have a course scheduled and colour the cells
*/
function colourCourses() {
    $('.cell').css("background-color", "#FFFFFF");
    course_ids = Object.keys(input_data.CourseData);
    for (let [index, course_key] of course_ids.entries()) {
        $('.'+course_key).css("background-color", course_colours[index]);
    }
}

/**
Shade a colour by a given amount
**/
function shadeColor(color, percent) {

    var R = parseInt(color.substring(1,3),16);
    var G = parseInt(color.substring(3,5),16);
    var B = parseInt(color.substring(5,7),16);

    R = parseInt(R * (100 + percent) / 100);
    G = parseInt(G * (100 + percent) / 100);
    B = parseInt(B * (100 + percent) / 100);

    R = (R<255)?R:255;
    G = (G<255)?G:255;
    B = (B<255)?B:255;

    var RR = ((R.toString(16).length==1)?"0"+R.toString(16):R.toString(16));
    var GG = ((G.toString(16).length==1)?"0"+G.toString(16):G.toString(16));
    var BB = ((B.toString(16).length==1)?"0"+B.toString(16):B.toString(16));

    return "#"+RR+GG+BB;
}

//Close the navigation menu
function closeNav() {
    document.getElementById("myNav").style.height = "0%";
}

/**
Download the (modified) schedule as a json file which can save intermediate progress
**/
function download(filename, text) {
  var element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}


