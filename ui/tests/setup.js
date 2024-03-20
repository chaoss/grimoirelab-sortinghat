// Mock ResizeObserver because it is unavailable in jsdom
// https://github.com/jsdom/jsdom/issues/3368
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

window.ResizeObserver = window.ResizeObserver || ResizeObserverStub;
