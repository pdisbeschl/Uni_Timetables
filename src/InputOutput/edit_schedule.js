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
var swap = false;
//cell, timeslot, course
var selected_course;
//Map that maps courses courses and if they have a conflict
var conflictMap = {};

//Wait until the html is loaded and fully generated
window.addEventListener('load', function () {
    closeNav();
    $("#download").click(function() { download("schedule_info.json",JSON.stringify(schedule_json));});
    $("#SwapButton").click(function() { set_swap_courses_true();});

    //Initialise click events for all table entries that they respond to clicks (
    for (var year in programmes) {
        var table = document.getElementById(programmes[year]);
        if (table != null) {
            for (var i = 0; i < table.rows.length; i++) {
                for (var j = 0; j < table.rows[i].cells.length; j++)
                    table.rows[i].cells[j].addEventListener("click", function() { selectCourse(this);
                                                                                  swap_courses(this);});
                }
            }
    }

    //Assigns each course a colour
    loadColourPalette();
    //Colours all the courses in the respective colour
    colourCourses();
})

/*
Click the swap menu button
*/
function set_swap_courses_true() {
    findConflicts(selected_course);
    colourCoursesGradient();
    swap = true;
}

/*
If the swap button was selected, we want to swap with the next course that was selected
*/
function swap_courses(cell) {
    //If we did not click the swap button we do not want to swap
    if (!swap) {
        return
    }
    //Get all the info we need to swap two classes
    cell1 = selected_course[0];
    timeslot1 = selected_course[1];
    course1 = selected_course[2];
    [cell2, timeslot2, course2] = getCourseInfo(cell);

    if(cell1.dataset.year != cell2.dataset.year) {
        return
    }

    //Remove course
    c1 = removeCourseFromSchedule(timeslot1, course1);
    c2 = removeCourseFromSchedule(timeslot2, course2);
    addCourseToSchedule(timeslot2, c1);
    addCourseToSchedule(timeslot1, c2);

    //Update the class of the cells
    updateCell(cell1, course1, cell2, course2);
    colourCourses();

    $(".overlay").css('max-height', '0%');
    selected_course = undefined;
    swap = false;
}

/*
Updates the cell content and classes when swapping two cells
*/
function updateCell(cell1, course1, cell2, course2) {
    room_cell_id1 = cell1.id.replace('course','room');
    room_cell_id2 = cell2.id.replace('course','room');
    room_cell1 = document.getElementById(room_cell_id1);
    room_cell2 = document.getElementById(room_cell_id2);
    if (course1 !== undefined) {
        $(cell1).removeClass(course1["CourseID"]);
        $(room_cell1).removeClass(course1["CourseID"]);
    }
    if (course2 !== undefined) {
        $(cell2).removeClass(course2["CourseID"]);
        $(room_cell2).removeClass(course2["CourseID"]);
    }
    if (course1 !== undefined) {
        $(cell2).addClass(course1["CourseID"]);
        $(room_cell2).addClass(course1["CourseID"]);
    }
    if (course2 !== undefined) {
        $(cell1).addClass(course2["CourseID"]);
        $(room_cell1).addClass(course2["CourseID"]);
    }

    temp = $(cell1).html();
    $(cell1).html($(cell2).html());
    $(cell2).html(temp);

    temp = $(room_cell1).html();
    $(room_cell1).html($(room_cell2).html());
    $(room_cell2).html(temp);

}

/**
Add a course to the new location
**/
function addCourseToSchedule(timeslot, course) {
    if (course !== undefined) {
        if(schedule_json[timeslot] === undefined) {
            schedule_json[timeslot] = [];
        }
        schedule_json[timeslot].push(course);
    }
}

/**
Remove a course from the schedule and return the removed course for insertion at the updated location
**/
function removeCourseFromSchedule(timeslot, course) {
    let c;
    if (schedule_json[timeslot] !== undefined && course !== undefined) {
        schedule_json[timeslot].forEach( (course_info, index) => {
        if(course_info['CourseID'] == course['CourseID']) {
                c = schedule_json[timeslot].splice(index,1)
            }
        })
    }
    if (c !== undefined) {
        return c[0]
    }
    return c;
}

/*
Iterate over the schedule and find conflicts, colouring them in the respective colour
*/
function findConflicts(course_info) {
    if (selected_course === undefined) {
        return
    }
    //Get all the elements in the schedule that we have.

    /*
    Case1: We clicked on a cell which has a course in it:
        For every cell we want to extract the teacher and the year. If the year is the same as the selected one and there
        is a course scheduled then we flag the cell as unavailable.
        If the year is not the same we check if the teacher is the same as from the selected cell
    Case2: We clicked on an empty cell:
        We can ignore the year check since it has no course scheduled
        We need
    */
    conflictMap = {};
    [current_cell, current_timeslot, current_course] = selected_course
    cells = $('.cell')

    for (i = 0; i < cells.length; i++) {
        //We want to ignore the room cells
        if (cells[i].id.includes('room')) {
            continue;
        }
        iter_cell = cells[i];
        [iter_cell, iter_timeslot, iter_course] = getCourseInfo(iter_cell)
        room_cell_id = iter_cell.id.replace('course','room');

        //We only need to check for the timeslots of the year. We can check if a lecturer is scheduled htrough the json data
        if(iter_cell.dataset.year != current_cell.dataset.year) {
            continue;
        }

        if(isHoliday(iter_timeslot)) {
            conflictMap[room_cell_id] = 3;
            continue;
        }

        //Can we move the course in the current timeslot to the selected timeslot
        if (hasLecturerOverlap(current_timeslot, iter_course)) {
            conflictMap[room_cell_id] = 2;
            continue;
        }

        //Can we move the selected course to the current timeslot
        if (hasLecturerOverlap(iter_timeslot, current_course)) {
            conflictMap[room_cell_id] = 1;
            continue;
        }

        else {
            conflictMap[room_cell_id] = 0;
        }
    }
}


function isHoliday(timeslot) {
    for(j = 0; j < input_data["Holidays"].length; j++) {
        day = timeslot.split(' ')[0];
        if(input_data["Holidays"][j].includes(day))
            return true;
    }
    return false
}

/**

**/
function hasLecturerOverlap(timeslot, course) {
    if(schedule_json[timeslot] === undefined || course === undefined) {
        return false;
    }
    else {
        for(j = 0; j < schedule_json[timeslot].length; j++) {
            if(schedule_json[timeslot][j]["ProgID"] != course["ProgID"]) {
                console.log("Test")
                lecturers = schedule_json[timeslot][j]["Lecturers"].split(';');
                for(k = 0; k < lecturers.length; k++) {
                    if(course["Lecturers"].includes(lecturers[k]))
                        return true;
                }
            }
        }
    }
    return false;
}

/**
Upon clicking on a cell highlight the cell and show the information about the course
**/
function selectCourse(cell) {
    //If we clicked the swap button we want to swap the course with another course
    if (swap) {
        return
    }
    //Get the course information
    [cell, timeslot, course] = getCourseInfo(cell);
    selected_course = [cell, timeslot, course];

    colourCourses();


    //If we clicked on the room we still want to colour the course and room cell of the clicked cell
    cells = document.getElementsByClassName(cell.classList[1]);
    for (var i = 0; i < cells.length; i++) {
        cells[i].style.backgroundColor= shadeColor(colour_palette[cid],-40);
    }

    //Wait until the course info container disappeared and then update the data
    $(".overlay").css('max-height', '0%');
    setTimeout(function(){
        //Show the overlay with the course information
        overlay = document.getElementById("CourseInfoOverlay")
        overlay.innerHTML = "";
        $('#myNav').css('background-color', colour_palette[cid]);
        para = document.createElement("p");
        para.style.width = "100%";
        info_entry = document.createTextNode('Timeslot: ' + timeslot);
        para.appendChild(info_entry);
        overlay.appendChild(para);

        for(c in course) {
            para = document.createElement("p");
            //para.style.width = "75%";
            info_entry = document.createTextNode(c + ': ' + course[c]);
            para.appendChild(info_entry);
            overlay.appendChild(para);
        }

        $('.EE').remove();
        rand = Math.floor(Math.random() * 400);
        if (rand == 0)
            img = $('#img').prepend('<img class="EE" src="https://i.imgur.com/ZZ7YDFU.jpg" onerror="this.style.display=\'none\'">');
        else if (rand == 1)
            img = $('#img').prepend('<img class="EE" src="https://i.imgur.com/L4FkiF2.jpg" onerror="this.style.display=\'none\'">');
        else if (rand == 2)
            img = $('#img').prepend('<img class="EE" src="https://i.imgur.com/kvxxZV3.jpg" onerror="this.style.display=\'none\'">');
        else if (rand == 3)
            img = $('#img').prepend('<img class="EE" src="https://i.imgur.com/18aZSAB.jpg" onerror="this.style.display=\'none\'">');
        $(".overlay").css('max-height', '35%');
    }, 200);


    return
}

/**
Returns the clicked cell, the timeslot of that cell and the course as in the schedule
**/
function getCourseInfo(cell) {
    //Get the course id - If we clicked on a room cell we just redirect to the course cell
    course_cell_id = cell.id.replace('room','course');
    course_cell = document.getElementById(course_cell_id);
    cid = course_cell.textContent;
    cid = cid.replace(/\s/g,'');

    //Get the timeslot that was clicked
    timeslot = cell.classList[0];
    timeslot = timeslot.replace('_',' ');

    //Query the courses scheduled on that timeslot in the schedule.json and get the data
    let course;
    //Query the courses scheduled on that timeslot in the schedule.json and get the data
    if (schedule_json[timeslot] !== undefined) {
        schedule_json[timeslot].forEach( (course_info, index) => {
            if(cid == course_info['CourseID']) {
        	    course = course_info;
            }
        })
    }

    return [course_cell, timeslot, course];
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
    cells = $('.cell');
    for (i = 0; i < cells.length; i++) {
        $(cells[i]).css("background", "#FFFFFF");
    }
    course_ids = Object.keys(input_data.CourseData);
    for (let [index, course_key] of course_ids.entries()) {
        $('.'+course_key).css("background-color", course_colours[index]);
    }
}

/*
Iterate over all cells of the year and colour them with a gradient indicating if they cause a conflict
*/
function colourCoursesGradient() {
///We should iterate over all the cells. If they have the same year we want to colour them in the colour they already have and add a red or green gradient
    cells = $('.cell');
    for (i = 0; i < cells.length; i++) {
        current_colour = $(cells[i]).css("background-color");
        if(conflictMap[cells[i].id] == undefined || cells[i].dataset.year != selected_course[0].dataset.year)
            continue
        if(conflictMap[cells[i].id] == 0) {
            $(cells[i]).css({background: 'linear-gradient(45deg, ' + current_colour + ' 0%,' + current_colour + ' 80%, rgba(0,255,0,1) 100%)'});
        }
        else if(conflictMap[cells[i].id] == 1) {
            $(cells[i]).css({background: 'linear-gradient(45deg, ' + current_colour + ' 0%,' + current_colour + ' 80%, rgba(255,0,0,1) 100%)'});
        }
        else if(conflictMap[cells[i].id] == 2) {
            $(cells[i]).css({background: 'linear-gradient(45deg, ' + current_colour + ' 0%,' + current_colour + ' 80%, rgba(255,165,0) 100%)'});
        }
        else if(conflictMap[cells[i].id] == 3) {
            $(cells[i]).css({background: 'linear-gradient(45deg, ' + current_colour + ' 0%,' + current_colour + ' 80%, rgba(100,65,165,1) 100%)'});
        }

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
    $(".overlay").css('max-height', '0%');
    setTimeout(function(){
        $(".overlay").css('height', 'auto');
    }, 200);
    swap = false;
    selected_course = undefined;
    colourCourses();
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
