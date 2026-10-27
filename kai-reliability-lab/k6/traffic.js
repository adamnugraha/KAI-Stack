import http from 'k6/http';
import { sleep, check } from 'k6';

const base = __ENV.BASE_URL || 'http://gateway';
export const options = {
  scenarios: {
    legacy: { executor: 'constant-vus', vus: 4, duration: '3m', exec: 'legacy' },
    modern: { executor: 'constant-vus', vus: 4, duration: '3m', exec: 'modern' },
  },
};
export function legacy() { call('/legacy/search'); }
export function modern() { call('/modern/search'); }
function call(path) {
  const r = http.get(`${base}${path}?origin=Jakarta&destination=Bandung`, { tags: { route: path }, timeout: '5s' });
  check(r, { 'HTTP response under 500': (res) => res.status < 500 });
  sleep(0.2);
}
