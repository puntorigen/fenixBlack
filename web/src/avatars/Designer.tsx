// src/avatars/Designer.ts

import { AvatarBase } from './AvatarBase';

export class Designer extends AvatarBase {
    initializeAttributes() {
        this.name = "Christian";
        this.role = "Designer";
        this.goal = "Create visually appealing and user-friendly designs.";
        this.backstory = "With a decade of experience in graphic and digital design, specializing in UX/UI and brand identity.";
    }
}
