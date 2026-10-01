import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',timeout:30000,fullyParallel:false,use:{baseURL:process.env.BASE_URL||'http://127.0.0.1:5173',headless:true,channel:process.env.CI?undefined:'msedge',viewport:{width:1440,height:1100},screenshot:'only-on-failure'},reporter:'list'});
