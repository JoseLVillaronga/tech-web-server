# 🔧 Guía de Patrones JavaScript para Web Server Python

## 📋 Patrones de Código Validados

Esta guía contiene los patrones de JavaScript que han sido **probados y validados** en nuestro web server Python estricto.

---

## 🎯 Patrón 1: Inicialización Robusta de Plugins jQuery

### ✅ Patrón Recomendado
```javascript
// Función de inicialización defensiva
function initializePlugin(pluginName, selector, config) {
  // 1. Verificar jQuery
  if (typeof $ === 'undefined') {
    console.error('jQuery no está disponible');
    return false;
  }
  
  // 2. Verificar plugin
  if (typeof $.fn[pluginName] === 'undefined') {
    console.error(`Plugin ${pluginName} no está disponible`);
    return false;
  }
  
  // 3. Verificar elementos DOM
  const elements = $(selector);
  if (elements.length === 0) {
    console.warn(`No se encontraron elementos: ${selector}`);
    return false;
  }
  
  // 4. Inicializar con manejo de errores
  try {
    elements[pluginName](config);
    return true;
  } catch (error) {
    console.error(`Error inicializando ${pluginName}:`, error);
    return false;
  }
}

// Uso del patrón
function initializeCarousels() {
  initializePlugin('owlCarousel', '#jlv1', {
    autoPlay: 3000,
    stopOnHover: true,
    lazyLoad: true,
    navigation: true,
    singleItem: true,
    autoHeight: true,
    transitionStyle: "fadeUp"
  });
  
  initializePlugin('owlCarousel', '#jlv2', {
    autoPlay: 3000,
    stopOnHover: true,
    lazyLoad: true,
    navigation: true,
    singleItem: true,
    autoHeight: true,
    transitionStyle: "fadeUp"
  });
}
```

---

## ⏱️ Patrón 2: Timing de Inicialización Múltiple

### ✅ Patrón Recomendado
```javascript
// Sistema de inicialización con múltiples puntos de entrada
class ComponentInitializer {
  constructor() {
    this.initialized = false;
    this.retryCount = 0;
    this.maxRetries = 3;
  }
  
  init() {
    if (this.initialized) return;
    
    // Verificar dependencias
    if (!this.checkDependencies()) {
      if (this.retryCount < this.maxRetries) {
        this.retryCount++;
        setTimeout(() => this.init(), 1000);
      }
      return;
    }
    
    // Inicializar componentes
    this.initializeComponents();
    this.initialized = true;
  }
  
  checkDependencies() {
    return typeof $ !== 'undefined' && 
           typeof $.fn.owlCarousel !== 'undefined';
  }
  
  initializeComponents() {
    // Lógica de inicialización aquí
    initializeCarousels();
  }
}

// Instanciar inicializador
const initializer = new ComponentInitializer();

// Múltiples puntos de entrada
$(document).ready(function() {
  setTimeout(() => initializer.init(), 2000);
});

window.addEventListener('load', function() {
  setTimeout(() => initializer.init(), 1000);
});

// Backup adicional para casos extremos
setTimeout(() => initializer.init(), 5000);
```

---

## 🔗 Patrón 3: Carga Ordenada de Dependencias

### ✅ Estructura HTML Recomendada
```html
<!DOCTYPE html>
<html>
<head>
  <!-- CSS primero -->
  <link rel="stylesheet" href="css/materialize.min.css">
  <link rel="stylesheet" href="owl-carousel/owl.carousel.css">
  <link rel="stylesheet" href="owl-carousel/owl.theme.css">
  <link rel="stylesheet" href="css/custom.css">
</head>
<body>
  <!-- Contenido HTML -->
  
  <!-- JavaScript al final del body -->
  <!-- 1. jQuery (base fundamental) -->
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  
  <!-- 2. Plugins de jQuery -->
  <script src="owl-carousel/owl.carousel.js"></script>
  
  <!-- 3. Frameworks CSS/JS -->
  <script src="js/materialize.min.js"></script>
  
  <!-- 4. Scripts personalizados -->
  <script src="js/custom.js"></script>
</body>
</html>
```

---

## 🛡️ Patrón 4: Manejo de Errores Avanzado

### ✅ Sistema de Error Handling
```javascript
// Sistema de manejo de errores para plugins
class PluginErrorHandler {
  static handle(pluginName, error, context = {}) {
    const errorInfo = {
      plugin: pluginName,
      error: error.message,
      stack: error.stack,
      context: context,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent
    };
    
    // Log estructurado
    console.group(`🚨 Error en ${pluginName}`);
    console.error('Mensaje:', error.message);
    console.error('Contexto:', context);
    console.error('Stack:', error.stack);
    console.groupEnd();
    
    // Opcional: enviar a sistema de logging
    // this.sendToLoggingService(errorInfo);
    
    return false;
  }
  
  static wrap(fn, pluginName, context = {}) {
    return function(...args) {
      try {
        return fn.apply(this, args);
      } catch (error) {
        return PluginErrorHandler.handle(pluginName, error, context);
      }
    };
  }
}

// Uso del error handler
const safeInitializeCarousel = PluginErrorHandler.wrap(
  function(selector, config) {
    $(selector).owlCarousel(config);
  },
  'owlCarousel',
  { component: 'carousel-initializer' }
);
```

---

## 🖼️ Patrón 5: Optimización de Imágenes

### ✅ Lazy Loading Híbrido
```html
<!-- HTML con lazy loading nativo -->
<div id="carousel" class="owl-carousel">
  <div class="item">
    <img src="placeholder.jpg" 
         data-src="real-image-1.jpg"
         loading="lazy"
         alt="Descripción de imagen 1">
  </div>
  <div class="item">
    <img src="placeholder.jpg" 
         data-src="real-image-2.jpg"
         loading="lazy"
         alt="Descripción de imagen 2">
  </div>
</div>
```

```javascript
// JavaScript con lazy loading del plugin
function initializeOptimizedCarousel(selector) {
  const config = {
    // Lazy loading del plugin
    lazyLoad: true,
    
    // Configuración de rendimiento
    autoPlay: 3000,
    stopOnHover: true,
    
    // Configuración visual
    navigation: true,
    singleItem: true,
    autoHeight: true,
    transitionStyle: "fadeUp",
    
    // Callbacks para optimización
    beforeInit: function() {
      // Precargar primera imagen
      const firstImg = this.$elem.find('img').first();
      if (firstImg.attr('data-src')) {
        firstImg.attr('src', firstImg.attr('data-src'));
      }
    },
    
    afterMove: function() {
      // Precargar siguiente imagen
      const nextImg = this.$elem.find('.active').next().find('img');
      if (nextImg.attr('data-src')) {
        nextImg.attr('src', nextImg.attr('data-src'));
      }
    }
  };
  
  return initializePlugin('owlCarousel', selector, config);
}
```

---

## 🔄 Patrón 6: Reinicialización Dinámica

### ✅ Sistema de Reinicialización
```javascript
// Gestor de componentes dinámicos
class ComponentManager {
  constructor() {
    this.components = new Map();
  }
  
  register(name, selector, initFn, config = {}) {
    this.components.set(name, {
      selector,
      initFn,
      config,
      initialized: false,
      instance: null
    });
  }
  
  initialize(name) {
    const component = this.components.get(name);
    if (!component) return false;
    
    try {
      // Destruir instancia anterior si existe
      if (component.initialized && component.instance) {
        this.destroy(name);
      }
      
      // Inicializar nueva instancia
      component.instance = component.initFn(component.selector, component.config);
      component.initialized = true;
      
      return true;
    } catch (error) {
      console.error(`Error inicializando ${name}:`, error);
      return false;
    }
  }
  
  destroy(name) {
    const component = this.components.get(name);
    if (!component || !component.initialized) return;
    
    try {
      // Destruir instancia de Owl Carousel
      if (component.instance && $(component.selector).data('owlCarousel')) {
        $(component.selector).data('owlCarousel').destroy();
      }
      
      component.initialized = false;
      component.instance = null;
    } catch (error) {
      console.error(`Error destruyendo ${name}:`, error);
    }
  }
  
  reinitialize(name) {
    this.destroy(name);
    return this.initialize(name);
  }
}

// Uso del gestor
const manager = new ComponentManager();

// Registrar componentes
manager.register('carousel1', '#jlv1', initializeOptimizedCarousel);
manager.register('carousel2', '#jlv2', initializeOptimizedCarousel);

// Inicializar todos los componentes
$(document).ready(function() {
  setTimeout(() => {
    manager.initialize('carousel1');
    manager.initialize('carousel2');
  }, 2000);
});
```

---

## 📊 Patrón 7: Monitoreo de Performance

### ✅ Sistema de Métricas
```javascript
// Monitor de rendimiento para componentes
class PerformanceMonitor {
  static measure(name, fn) {
    const start = performance.now();
    
    try {
      const result = fn();
      const end = performance.now();
      const duration = end - start;
      
      console.log(`⏱️ ${name}: ${duration.toFixed(2)}ms`);
      
      // Alertar si es muy lento
      if (duration > 1000) {
        console.warn(`🐌 ${name} tardó ${duration.toFixed(2)}ms (>1s)`);
      }
      
      return result;
    } catch (error) {
      const end = performance.now();
      const duration = end - start;
      console.error(`❌ ${name} falló después de ${duration.toFixed(2)}ms:`, error);
      throw error;
    }
  }
}

// Uso del monitor
function monitoredInitializeCarousels() {
  PerformanceMonitor.measure('Carousel Initialization', () => {
    initializeCarousels();
  });
}
```

---

## 🎯 Checklist de Implementación

### ✅ Antes de implementar cualquier plugin:

- [ ] **Verificar orden de carga** (jQuery → Plugin → Framework → Custom)
- [ ] **Implementar verificación de dependencias**
- [ ] **Agregar manejo de errores**
- [ ] **Configurar múltiples puntos de inicialización**
- [ ] **Implementar timeouts apropiados**
- [ ] **Verificar existencia de elementos DOM**
- [ ] **Agregar lazy loading si aplica**
- [ ] **Testear en web server estricto**

---

**Fecha:** 2025-06-19  
**Validado en:** Web Server Python Estricto  
**Estado:** ✅ Patrones Probados y Documentados
