(function(){

if(!('fetch' in window)){
    return
}
fetch('/api/about').then(r => r.json()).then(j =>  {
    let ident = document.querySelector('#ident');
    ident.textContent = j.service
    if(j.version){
        ident.textContent += ' ' + j.version
    }
})

})();
