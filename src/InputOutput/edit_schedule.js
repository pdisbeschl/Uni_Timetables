//Wait until the html is loaded and fully generated
window.addEventListener('load', function () {
    //document.getElementById('BAY1').style.backgroundColor="red";
    var programmes = ['BAY1','BAY2','BAY3','MAAIY1','MADSDMY1'];
    for (var year in programmes) {
        var table = document.getElementById(programmes[year]);
        if (table != null) {
            for (var i = 0; i < table.rows.length; i++) {
                for (var j = 0; j < table.rows[i].cells.length; j++)
                    table.rows[i].cells[j].onclick = function () { getval(this); };
                }
            }
    }
    function getval(cel) {
        cel.style.backgroundColor="grey";
        //alert(cel.innerHTML);
    }
})