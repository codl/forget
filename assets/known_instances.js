const STORAGE_KEY = 'forget_known_instances';

export function known_save(known){
    localStorage.setItem(STORAGE_KEY, JSON.stringify(known));
}

export function known_load(){
    let known = localStorage.getItem(STORAGE_KEY);
    if(known){
        known = JSON.parse(known);
    }
    return known;
}
