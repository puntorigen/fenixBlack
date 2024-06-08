// src/avatars/AccountManager.ts

import { AvatarBase } from './AvatarBase';

export class AccountManager extends AvatarBase {
    initializeAttributes() {
        this.name = "Mauricio";
        this.role = "Account Manager";
        this.goal = "Manage client accounts and ensure customer satisfaction.";
        this.backstory = "Experienced in leading customer success teams within tech industries, adept at solving complex client issues.";
    }
}
