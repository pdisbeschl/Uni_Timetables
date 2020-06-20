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
var colour_palette = {"cell":"#FFFFFF"};
var swap = false;
//cell, timeslot, course
var selected_course;
//Map that maps courses courses and if they have a conflict
var conflictMap = {};

//Wait until the html is loaded and fully generated
window.addEventListener('load', function () {
    closeNav();

    //Make sure colours are printed
    document.body.setAttribute("style","-webkit-print-color-adjust: exact; margin-bottom: 15%");

    $("#download").click(function() { download("schedule_info.json");});
    $("#SwapButton").click(function() { set_swap_courses_true();});
    $("#EditButton").click(function() { loadCourseEditMenu();});
    $("#DeleteButton").click(function() { deleteCourse();});
    $("#closeEditMenu").click(function() { closeEditMenu();});
    $("#SaveEdit").click(function() { saveEditedCourse();});
    $(".AdditionalInfoButton").click(function() { addTextField(this);});

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

function deleteCourse() {
    if (selected_course[2] === undefined) {
        return
    }

    removeCourseFromSchedule(selected_course[1],selected_course[2]);
    let room_id = selected_course[0].id.replace('course', 'room')
    let room_cell = document.getElementById(room_id);
    room_cell.innerHTML = "";
    selected_course[0].innerHTML = "";
    $(selected_course[0]).removeClass(selected_course[2]["CourseID"]);
    $(room_cell).removeClass(selected_course[2]["CourseID"]);
    colourCourses();
}

function saveEditedCourse() {
    form = document.getElementById("CourseData").elements;
    let formMap = {}

    for (i = 0; i < form.length; i++) {
        if(form[i].value == "") {
            formMap[form[i].id] = form[i].placeholder;
        }
        else {
            formMap[form[i].id] = form[i].value;
        }
    }
    //Replace the course entry
    if(selected_course[2] !== undefined) {
        cid = selected_course[2]["CourseID"];
    }
    else {
        cid = formMap["CourseID"];
    }
    selected_course[0].innerHTML = formMap["CourseID"]

    //Replace the
    let room_id = selected_course[0].id.replace('course', 'room')
    let room_cell = document.getElementById(room_id);
    room_cell.innerHTML = formMap["RID"];

    //Update the roomid of the scheduled course
    //removeCourseFromSchedule(selected_course[1], selected_course[2]);
    editedCourse = {};
    editedCourse["Conflict"] = false;
    editedCourse["CourseID"] = formMap["CourseID"];
    editedCourse["Lecturers"] = formMap["Lecturers"];
    editedCourse["Name"] = formMap["Course name"];
    editedCourse["ProgID"] = formMap["Programme"];
    editedCourse["RoomID"] = formMap["RID"];

    removeCourseFromSchedule(selected_course[1], editedCourse);
    addCourseToSchedule(selected_course[1], editedCourse);

    colour_palette[cid] = formMap["Colour"];

    if(selected_course[2] === undefined) {
        $(selected_course[0]).addClass(cid);
        $(room_cell).addClass(cid);
    }

    set_print_cells(document.getElementById("print").checked);

    delete formMap["RID"]
    delete formMap["CourseID"]
    delete formMap["Colour"]
    delete formMap["print"]

    //Update the plandata of the course
    input_data["CourseData"][cid] = formMap;
    input_data["CourseColours"] = colour_palette;

    closeEditMenu();
    colourCourses();
}

function set_print_cells(printing) {
    cells = $('.cell')

    for (i = 0; i < cells.length; i++) {
        if(cells[i].classList.contains(selected_course[2]["CourseID"])) {
            if(printing) {
                $(cells[i]).removeClass("no-print-course");
            }
            else {
                $(cells[i]).removeClass(selected_course[2]["CourseID"]);
                $(cells[i]).addClass("no-print-course");
                $(cells[i]).addClass(selected_course[2]["CourseID"]);
            }
        }
    }
}

/*
When the edit course button is clicked we want to show the course edit menu
*/
function loadCourseEditMenu() {
    let course
    if(selected_course[2] === undefined) {
        course = input_data["CourseData"][Object.keys(input_data["CourseData"])[0]];
    }
    else {
        course = input_data["CourseData"][selected_course[2]["CourseID"]];
    }
    buildEditMenuFields(course);
    if(selected_course[2] === undefined) {
        form = document.getElementById("CourseData").elements;
        for (i = 0; i < form.length; i++) {
            form[i].placeholder = "";
        }
    }

    //Setup animation for the menu
    let editMenu = document.getElementById("EditCourse")
    $(editMenu).css('visibility', 'unset');
    $(editMenu).css('transition', 'width 0.25s ease-out, height 0.25s ease-in 0.25s');
    $(editMenu).css('height', '65%');
    $(editMenu).css('width', '30%');
    $(editMenu).css('background-color', colour_palette[selected_course[2]["CourseID"]]);

}

function buildEditMenuFields(course) {
    textfield_timeslot = document.getElementById("editMenuTimeslot");
    textfield_timeslot.innerHTML = selected_course[1];

    let dataForm = document.getElementById("CourseData");
    dataForm.innerHTML = "";
    cid = selected_course[0].innerHTML.replace(/\s/g,'')

    //Create Course field
    textfield = document.createElement("label");
    let t = document.createTextNode("Course Code (text)");
    textfield.setAttribute("for", "CID");
    textfield.appendChild(t);
    textfield.setAttribute('class', 'editLabel');
    dataForm.appendChild(textfield);

    inputfield = document.createElement("input");
    inputfield.setAttribute('type', 'text');
    inputfield.setAttribute('placeholder', cid);
    inputfield.setAttribute('id', "CourseID");
    inputfield.setAttribute('class', 'editInput');
    dataForm.appendChild(inputfield);

    //Create Room Field
    textfield = document.createElement("label");
    t = document.createTextNode("RoomID");
    textfield.setAttribute("for", "RoomID");
    textfield.appendChild(t);
    textfield.setAttribute('class', 'editLabel');
    dataForm.appendChild(textfield);

    inputfield = document.createElement("input");
    inputfield.setAttribute('type', 'text');
    let room_id = selected_course[0].id.replace('course', 'room')
    let room_cell = document.getElementById(room_id);
    inputfield.setAttribute('placeholder', room_cell.innerHTML);
    inputfield.setAttribute('id', "RID");
    inputfield.setAttribute('class', 'editInput');
    dataForm.appendChild(inputfield);

    //Create Color Field
    textfield = document.createElement("label");
    t = document.createTextNode("Course Colour");
    textfield.setAttribute("for", "Colour");
    textfield.appendChild(t);
    textfield.setAttribute('class', 'editLabel');
    dataForm.appendChild(textfield);

    inputfield = document.createElement("input");
    inputfield.setAttribute('type', 'color');
    inputfield.setAttribute('id', "Colour");
    inputfield.setAttribute('value', colour_palette[cid]);
    inputfield.setAttribute('class', 'editInput');
    dataForm.appendChild(inputfield);

    for(c in course) {
        textfield = document.createElement("label");
        t = document.createTextNode(c);
        textfield.setAttribute("for", c);
        textfield.appendChild(t);
        textfield.setAttribute('class', 'editLabel');
        dataForm.appendChild(textfield);

        inputfield = document.createElement("input");
        inputfield.setAttribute('type', 'text');
        inputfield.setAttribute('placeholder', course[c]);
        inputfield.setAttribute('id', c);
        inputfield.setAttribute('class', 'editInput');
        dataForm.appendChild(inputfield);
    }

    //Create Print checkbox
    textfield = document.createElement("label");
    t = document.createTextNode("Print course");
    textfield.setAttribute("for", "Colour");
    textfield.appendChild(t);
    textfield.setAttribute('class', 'editLabel');
    dataForm.appendChild(textfield);

    inputfield = document.createElement("INPUT");
    inputfield.setAttribute("type", "checkbox");
    currently_printing = "no-print" in selected_course[0].classList
    inputfield.checked = !currently_printing;
    inputfield.setAttribute('id', "print");
    dataForm.appendChild(inputfield);

}

//Close the edit menu
function closeEditMenu() {
    //Setup animation for the menu
    $("#EditCourse").css('transition', 'width 0.25s ease-in 0.25s, height 0.25s ease-out');
    $("#EditCourse").css('height', '5%');
    $("#EditCourse").css('width', '0%');
    setTimeout(function(){
    $("#EditCourse").css('visibility', 'hidden');
    }, 500);
}

/*
Click the swap menu button
*/
function set_swap_courses_true() {
    if (swap) {
        return;
    }
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

        if(isLecturerUnavailable(room_cell_id, iter_timeslot, current_course)) {
            conflictMap[room_cell_id] = 5;
        }

        if(isLecturerUnavailable(room_cell_id, current_timeslot, iter_course)) {
            conflictMap[room_cell_id] = 4;
        }


        if(isHoliday(room_cell_id, iter_timeslot)) {
            conflictMap[room_cell_id] = 3;
        }

        //Can we move the course in the current timeslot to the selected timeslot
        if (hasLecturerOverlap(room_cell_id, current_timeslot, iter_course)) {
            conflictMap[room_cell_id] = 2;
        }

        //Can we move the selected course to the current timeslot
        if (hasLecturerOverlap(room_cell_id, iter_timeslot, current_course)) {
            conflictMap[room_cell_id] = 1;
            continue;
        }

        if (conflictMap[room_cell_id] === undefined) {
            conflictMap[room_cell_id] = 0;
        }
    }
}

/**
Check if a lecturer is unavailable at a timeslot
**/
function isLecturerUnavailable(i_cell, timeslot, course) {
    if (course === undefined) {
        return false
    }
    lecturers = course["Lecturers"].split(';');
    for(j = 0; j < lecturers.length; j++) {
        lecturer = lecturers[j].replace(/\s/g,'');
        if(input_data["LecturerData"][lecturer] !== undefined) {
            unavailable_dates = input_data["LecturerData"][lecturer];
            for(k = 0; k < unavailable_dates.length; k++) {
                if(timeslot == unavailable_dates[k]) {
                    room = document.getElementById(i_cell)
                    current_tooltip = $(room).attr('title');
                    if(current_tooltip === undefined)
                        current_tooltip = "";
                    $(room).attr('title', current_tooltip + "\n" + lecturer + " is not available on " + timeslot);
                    return true
                }
            }
        }
    }
    return false
}

function isHoliday(i_cell, timeslot) {
    day = timeslot.split(' ')[0];
    for(j = 0; j < input_data["Holidays"].length; j++) {
        if(input_data["Holidays"][j].includes(day)) {
            room = document.getElementById(i_cell)
            current_tooltip = $(room).attr('title');
            if(current_tooltip === undefined)
                current_tooltip = "";
            $(room).attr('title', current_tooltip + "\n" + timeslot + " is a holiday");
            return true;
        }
    }
    return false
}

/**

**/
function hasLecturerOverlap(i_cell, timeslot, course) {
    if(schedule_json[timeslot] === undefined || course === undefined) {
        return false;
    }
    else {
        for(j = 0; j < schedule_json[timeslot].length; j++) {
            if(schedule_json[timeslot][j]["ProgID"] != course["ProgID"]) {
                lecturers = schedule_json[timeslot][j]["Lecturers"].split(';');
                for(k = 0; k < lecturers.length; k++) {
                    if(course["Lecturers"].includes(lecturers[k])) {
                        room = document.getElementById(i_cell)
                        current_tooltip = $(room).attr('title');
                        if(current_tooltip === undefined)
                            current_tooltip = "";
                        $(room).attr('title', current_tooltip + "\n" + lecturers[k] + " is a already teaching " + schedule_json[timeslot][j]["CourseID"] + " on the " + timeslot);
                        return true;
                    }
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
    closeEditMenu();
    //If we clicked the swap button we want to swap the course with another course
    if (swap) {
        return
    }
    //Get the course information
    [cell, timeslot, course] = getCourseInfo(cell);
    selected_course = [cell, timeslot, course];

    if(course === undefined) {
        $("#EditButton").text("New Course");
    }
    else {
        $("#EditButton").text("Edit");
    }

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

        for(c in input_data["CourseData"][cid]) {
            para = document.createElement("p");
            //para.style.width = "75%";
            info_entry = document.createTextNode(c + ': ' + input_data["CourseData"][cid][c]);
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
    cid = course_cell.classList[course_cell.classList.length-1]//textContent;
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
    if (input_data["CourseColours"] !== undefined) {
        colour_palette = input_data["CourseColours"];
        return
    }
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
    let colour;
    for (i = 0; i < cells.length; i++) {
        $(cells[i]).css("background", "#FFFFFF");
        $(cells[i]).removeAttr('title');
    }
    course_ids = Object.keys(input_data.CourseData);
    for (let [index, course_key] of course_ids.entries()) {
        $('.'+course_key).css("background-color", colour_palette[course_key]);
    }
}

/*
Iterate over all cells of the year and colour them with a gradient indicating if they cause a conflict
*/
function colourCoursesGradient() {
///We should iterate over all the cells. If they have the same year we want to colour them in the colour they already have and add a red or green gradient
    cells = $('.cell');
    //0 - green = free; 1 - red selected teacher teaches at other timeslot;  2 - orange other teacher teaches at selected timeslot
    //3 - purple = holiday; 4 - cyan = selected teacher is unav. at other timeslot; 5 - blue = other teacher is unav. at selected timeslot
    conflict_colours = ["#00ff00", "#ff0000", "#ffa600", "#ff00ff", "#00ffff", "#0000ff"];
    for (i = 0; i < cells.length; i++) {
        current_colour = $(cells[i]).css("background-color");
        if(conflictMap[cells[i].id] == undefined || cells[i].dataset.year != selected_course[0].dataset.year)
            continue
        else {
            $(cells[i]).css({background: 'linear-gradient(45deg, ' + current_colour + ' 0%,' + current_colour + ' 80%, '+ conflict_colours[conflictMap[cells[i].id]] + ' 100%)'});
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
function download(filename) {
  download_string = JSON.stringify(schedule_json) + "\n" + JSON.stringify(input_data);
  var element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(download_string));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}

/**
Add a textfield which holds additional information
**/
function addTextField(button) {
    info_box = document.getElementById('additional-info_' + button.dataset.year);
    var textfield = document.createElement("input");
    info_box.prepend(textfield);
    $(textfield).css("width", "100%");
    $(textfield).addClass("info-field");
}