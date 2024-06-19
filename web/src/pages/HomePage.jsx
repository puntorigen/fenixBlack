import React, { useRef, useState } from 'react';
import { WiredCard, WiredButton, WiredInput } from 'react-wired-elements';
import { brandSchema, brochureSchema, privacyPolicy } from '../schemas';
import { tools } from '../experts/constants';

import Meeting from '../components/Meeting';
import AccountManager from '../experts/AccountManager';
import Designer from '../experts/Designer';
import Lawyer from '../experts/Lawyer';
import ResearchAnalyst from '../experts/ResearchAnalyst';
import LeadMarketAnalyst from '../experts/Marketing/LeadMarketAnalyst';

function HomePage() {
    return (<h1>Home Page</h1>);
}

export default HomePage;