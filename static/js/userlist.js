
function filterFunction() {
  var input, filter, div, a, txtValue;
  input = document.getElementById("userFilter");
  filter = input.value.toUpperCase();
  div = document.getElementById("userList");
  a = div.getElementsByTagName("option");
  for (i = 0; i < a.length; i++) {
    txtValue = a[i].innerText;
    if (txtValue.toUpperCase().indexOf(filter) > -1) {
      a[i].style.display = "";
    } else {
      a[i].style.display = "none";
      a[i].selected = false;
    }
  }
}
