//Load the json schedule from the schedule_info.js file
var schedule_json = schedule;
var input_data = input_raw;
var programmes = ['BAY1','BAY2','BAY3','MAAIY1','MADSDMY1'];
var course_colours = ['#FFB5E8', '#B28DFF', '#DCD3FF', '#AFF8D8', '#BFFCC6', '#FFC9DE', '#FF9CEE', '#C5A3FF', '#A79Aff', '#C4FAF8',
               '#DBFFD6', '#FFABAB', '#FFCCF9', '#D5AAFF', '#B5B9FF', '#85E3FF', '#F3FFE3', '#FFBEBC', '#FCC2FF', '#ECD4FF',
               '#97A2FF', '#ACE7FF', '#E7FFAC', '#FFCBC1', '#F6A6FF', '#FBE4FF', '#AFCBFF', '#6EB5FF', '#FFFFD1', '#FFF5BA'];
var colour_palette = {};

//Wait until the html is loaded and fully generated
window.addEventListener('load', function () {
    var btn = document.createElement("BUTTON");
    btn.innerHTML = "Download";                   // Insert text
    btn.onclick = function () { download("schedule_info.js",JSON.stringify(schedule_json)); };
    document.body.appendChild(btn);

    //document.getElementById('BAY1').style.backgroundColor="red";
    for (var year in programmes) {
        var table = document.getElementById(programmes[year]);
        if (table != null) {
            for (var i = 0; i < table.rows.length; i++) {
                for (var j = 0; j < table.rows[i].cells.length; j++)
                    table.rows[i].cells[j].onclick = function () { getCourseInfo(this); };
                }
            }
    }
    loadColourPalette();
    colourCourses();

    function load() {
        var someData_notJSON = JSON.parse(out.json);

    }

    function getCourseInfo(cell) {
        document.getElementById("myNav").style.height = "0%";
        colourCourses();

        //Get the course id
        course_cell_id = cell.id.replace('room','course');
        course_cell = document.getElementById(course_cell_id);
        cid = course_cell.textContent;
        cid = cid.replace(/\s/g,'');

        //Get the timeslot that was clicked
        timeslot = cell.classList[0];
        timeslot = timeslot.replace('_',' ');
        let course;

        if (schedule_json[timeslot] !== undefined) {
            schedule_json[timeslot].forEach( (course_info, index) => {
        		if(cid == course_info['CourseID']) {
        		    console.log(course_info);
        		    course = course_info;
        		}
            })
        }
        if (course === undefined) {
            return
        }
        cells = document.getElementsByClassName(cell.classList[1]);
        for (var i = 0; i < cells.length; i++) {
            cells[i].style.backgroundColor="grey";
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
        setTimeout(function(){ document.getElementById("myNav").style.height = "25%"}, 200);
        //alert(cel.innerHTML);
        return course;
    }
})

function loadColourPalette() {
    course_ids = Object.keys(input_data.CourseData);
    for (let [index, course_key] of course_ids.entries()) {
        colour_palette[course_key] = course_colours[index];
    }

}

function colourCourses() {
    resetSelected();
    course_ids = Object.keys(input_data.CourseData);
    for (let [index, course_key] of course_ids.entries()) {
        $('.'+course_key).css("background-color", course_colours[index]);
    }
}

function resetSelected() {
    for (var year in programmes) {
        var table = document.getElementById(programmes[year]);
        if (table != null) {
            for (var i = 0; i < table.rows.length; i++) {
                for (var j = 0; j < table.rows[i].cells.length; j++)
                    table.rows[i].cells[j].style.backgroundColor = "#FFFFFF";
                }
            }
    }
}

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


