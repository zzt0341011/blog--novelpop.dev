/* Local search
*/
var input = document.getElementById("search-input");
var resultsList = document.getElementById('search-results');
var items = resultsList.getElementsByTagName("li");
// Define a debounce function to avoid triggering input events too often
function debounce(fn, delay) {
    var timer = null; // Define a timer
    return function() {
        var context = this; // Save the this reference
        var args = arguments; // Save the arguments
        clearTimeout(timer); // Clear the previous timer
        timer = setTimeout(function() { // Set a new timer
            fn.apply(context, args);
        }, delay); // Delay
    }
}
// Get the matched characters from the pinyin-pro match indexes
function getMatchedWord(text, index) {
    // If the index is a number, return the character at that position
    if (index == Number(index)) {
        return text[index];
    }   
    // If the index is an array, return the string in that range
    if (Array.isArray(index)) {
        var result = "";
        for (var i = 0; i < index.length; i++) {
            result += text.charAt(index[i]);
        }
        return result;
    }  
    return '';
}
// Search logic
function search() {
    var keyword = this.value;  
    if (keyword.trim() === '') { // Check whether the keyword is empty or only whitespace   
        resultsList.innerHTML = '<span>Search this page</span>';  // Clear the results list  
        return;  
    }
    if (encodeURIComponent(keyword.trim()).length === 1) { // Check the keyword length  
        resultsList.innerHTML = '<span><strong>Tip:</strong> Enter at least 2 letters or digits</span>';
        return;  
    }    
    var xCards = document.getElementsByClassName('xe-card');  
    var results = []; // Store the matching results
    let regex = new RegExp(keyword, 'i'); // The 'i' flag means case-insensitive     
    if (typeof pinyinPro !== 'undefined') { //https://pinyin-pro.cn/use/match.html
        var { match:pyMatch } = pinyinPro;
    } 
    for (var i = 0; i < xCards.length; i++) {  
        var cardLink = xCards[i].querySelector('a');  
        // Get the text of the <a> tags with classes overflowClip_1 and overflowClip_2
        var clipContent = cardLink.querySelector('.overflowClip_1').textContent.trim() + " - " + cardLink.querySelector('.overflowClip_2').textContent.trim();
        var imgSrc = cardLink.querySelector('img').getAttribute('data-src'); 
        if (cardLink) {
            // Regular match
            let wordMatch = clipContent.match(regex);
            // Pinyin match
            if (pyMatch !== undefined && /^[a-zA-Z0-9]/.test(keyword)) { 
               var pinyinMatch = pyMatch(clipContent, keyword, { continuous: true, precision: 'start'});
            }
            if (wordMatch || pinyinMatch ) {
                // Add the matched content to the results array   
                results.push({
                    href: cardLink.href,
                    text: clipContent,
                    dataSrc: imgSrc,
                    pyMatch: pinyinMatch,
                    wdMatch: wordMatch
                });  
            }  
        }  
    }  
    
    resultsList.innerHTML = '';  // Clear the results list
    if (results.length > 0) {
        var defaultLogo = rootPath+'images/favicon.png';
        for (var j = 0; j < results.length; j++) {
        // Replace the matched characters with highlighted tags
            if (results[j].wdMatch){
                var word = results[j].wdMatch[0];
            }else{
                var word = getMatchedWord(results[j].text, results[j].pyMatch);
            }
            var highlight = "<strong>" + word + "</strong>";
            var newtext = results[j].text.replace(word, highlight);;
        // Results list
            var listItem = document.createElement('li');  
            // Add an <i> tag to display the logo
            var newIcon = document.createElement('i');
            var img = document.createElement('img');
            img.classList.add('lazy');
            img.src = defaultLogo;
            img.setAttribute('data-src',results[j].dataSrc)
            img.setAttribute('onerror', `javascript:this.src='${defaultLogo}'`);
            newIcon.appendChild(img);
            // Add an <a> tag
            var newLink = document.createElement('a');  
            newLink.href = results[j].href;  
            newLink.innerHTML = newtext;                      
            newLink.target = "_blank";
            // Add the new element to the search results list
            listItem.appendChild(newIcon);
            listItem.appendChild(newLink);  
            resultsList.appendChild(listItem);  
        }
        $("img.lazy").lazyload();
    } else {  
        resultsList.innerHTML = '<span>No matching content found.</span>';        
    }
}
// Add an input event listener, wrapping the search function in a debounce with a 300ms delay
input.addEventListener("input", debounce(search, 300));

/* Search button: open the search box */
document.getElementById('search-btn').addEventListener('click', function() {  
    var searchBox = document.getElementById('overlay');  
    if (searchBox.style.display === 'none') {  
    searchBox.style.display = 'block';
    var inputElement = document.getElementById('search-input');  
    inputElement.focus(); 
    } else {  
    searchBox.style.display = 'none';
    }  
});
/* Ctrl+F: open the search box */
document.addEventListener('keydown', function(event) { 
    var searchBox = document.getElementById('overlay');
    var inputElement = document.getElementById('search-input');  
    if (event.ctrlKey && event.key === 'f') { // CTRL+F  
        if (searchBox.style.display === 'none') {               
            searchBox.style.display = 'block';
            inputElement.focus();
            event.preventDefault(); // Prevent the default behavior 
        }else{
            searchBox.style.display = 'none';
            event.preventDefault();
        }
    }  
});
/* Click on empty space: close the search box */
document.getElementById('overlay').addEventListener('click', function(event) {  
    var searchBox = document.getElementById('search-box');   
    if (!searchBox.contains(event.target)) {
    // The click was not on the search box itself or one of its children  
    this.style.display = 'none';
    }  
});
/* Search box close button */
document.getElementById('close-button').addEventListener('click', function(event) {
     var searchBox = document.getElementById('overlay'); 
     searchBox.style.display = 'none';
});
/* Keyboard events: select from the results list */        

var index = -1; // Currently selected index
document.addEventListener("keydown", function (event) {
    // If the up arrow is pressed
    if (event.key === 'ArrowUp') {
        // If nothing is selected, or the first item is selected, select the last item
        if (index == -1 || index == 0) {
            index = items.length - 1;
        } else {
            index--;// Otherwise, select the previous item
        }
        // Loop through all items, highlight the selected one and remove the highlight from the others
        for (var i = 0; i < items.length; i++) {
            if (i == index) {
                items[i].classList.add("highlight");
                // Scroll to the selected item
                items[i].scrollIntoView();
            } else {
                items[i].classList.remove("highlight");
            }
        }
    }
    // If the down arrow is pressed
    if (event.key === 'ArrowDown') {
        var height = items[0].offsetHeight; // Height of each li
        var visible = Math.floor(resultsList.clientHeight / height); // Number of li elements visible in the viewport
        if (index == -1 || index == items.length - 1) {
            index = 0;
        } else {
            index++;// Otherwise, select the next item
        }
        // Loop through all items, highlight the selected one and remove the highlight from the others
        for (var i = 0; i < items.length; i++) {
            if (i == index) {
                items[i].classList.add("highlight");
                // If the selected item is the first or last visible item, scroll to it
                if (i % visible == 0 || i % visible == visible - 1) {
                    // Scroll to the selected item
                    items[i].scrollIntoView();
                }
            } else {
                items[i].classList.remove("highlight");
            }
        }
    }
    // If Enter is pressed
    if (event.key === 'Enter') {
        // If an item is selected, trigger a click on its link
        if (index != -1) {
            var link = items[index].getElementsByTagName("a")[0];
            link.click();
        }
    }
});
