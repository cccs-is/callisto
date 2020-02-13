$(document).ready(function(){
    $("#previewModal").on('show.bs.modal', function (e) {
      var nbid = $(e.relatedTarget).data('nbid');
      var nbtitle = $(e.relatedTarget).data('nbtitle');
      console.log(nbtitle);
      console.log($('#nbtitle_fill').html);
      $('#document_filler').load('/render-document/'+nbid);
      $('#nbtitle_fill').html(nbtitle);
      $('#nbopenId').attr("href", '/open-document/'+nbid);
      $('#detailId').attr("href", '/document/'+nbid);
    });
    $('[data-toggle="tooltip"]').tooltip();
});
