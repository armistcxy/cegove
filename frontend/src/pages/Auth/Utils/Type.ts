export interface RegistrationForm {
    fullName: string;
    email: string;
    phone: string;
    password: string;
    dob: string;
    address: string;
    district: string;
    city: string;
    gender: "MALE" | "FEMALE" | "OTHER";
    img: File;
}

export interface LoginForm {
    username: string;
    password: string;
}

