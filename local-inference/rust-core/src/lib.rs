use pyo3::prelude::*;
use pyo3::types::PyDict;

mod tensorrt;
mod preprocessing;
mod network;

use tensorrt::TensorRTInference;
use preprocessing::Preprocessor;
use network::NeuralNetwork;

/// Основной класс для инференса с использованием Rust-оптимизации
#[pyclass]
pub struct RustInferenceEngine {
    tensorrt_engine: Option<TensorRTInference>,
    preprocessor: Preprocessor,
    network: NeuralNetwork,
}

#[pymethods]
impl RustInferenceEngine {
    #[new]
    fn new(model_path: &str, use_tensorrt: bool) -> PyResult<Self> {
        let tensorrt_engine = if use_tensorrt {
            Some(TensorRTInference::new(model_path)?)
        } else {
            None
        };

        Ok(RustInferenceEngine {
            tensorrt_engine,
            preprocessor: Preprocessor::new()?,
            network: NeuralNetwork::new()?,
        })
    }

    /// Выполнить инференс на основе входного текста
    fn generate(&mut self, input_text: &str, max_length: usize) -> PyResult<String> {
        // Предварительная обработка текста
        let processed_input = self.preprocessor.process(input_text)?;
        
        // Выбор движка для инференса
        let result = if let Some(ref mut engine) = self.tensorrt_engine {
            // Используем TensorRT для ускорения
            engine.infer(&processed_input, max_length)?
        } else {
            // Используем стандартный нейронный движок
            self.network.infer(&processed_input, max_length)?
        };

        Ok(result)
    }

    /// Проверить, поддерживается ли CUDA
    fn is_cuda_available(&self) -> PyResult<bool> {
        Ok(self.network.is_cuda_available()?)
    }

    /// Получить информацию о производительности
    fn get_performance_stats(&self) -> PyResult<Py<PyDict>> {
        Python::with_gil(|py| {
            let dict = PyDict::new(py);
            dict.set_item("tensorrt_enabled", self.tensorrt_engine.is_some())?;
            dict.set_item("cuda_available", self.network.is_cuda_available()?)?;
            Ok(dict.into())
        })
    }
}

/// Инициализация модуля
#[pymodule]
fn chatbot_inference(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RustInferenceEngine>()?;
    Ok(())
}