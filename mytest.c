fn p1(mut a: i32, mut b: i32) {
    let mut c:i32;
    c = a + b * c + 1;
    if c > 10 {
        c = 0;
    } else if c < 5 {
        c = 1;
    } else {
        c = 2;
    }
    while c < 5 {
        c = c + 1;
    }
}

fn main() {
    let mut a: i32 = 3;
    let mut b: i32 = 4;
    a = p1(a, b);
}