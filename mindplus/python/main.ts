// Mind+ V1.7.1+ Python mode extension for StarBridge Protocol V2.
// Mind+ V1 embeds Python 3.5, so generated programs use the bundled
// starbridge_mindplus compatibility module instead of the Python 3.10+ SDK.

//% color="#1677ff" iconWidth=50 iconHeight=40
namespace starbridge {

    //% block="连接星核板 V2（自动识别串口）" blockType="command"
    export function beginAuto(parameter: any, block: any) {
        addImports();
        Generator.addCode(`board = Board.begin(BoardType.STARCORE_V2)`);
    }

    //% block="连接星核板 V2 串口 [PORT]" blockType="command"
    //% PORT.shadow="string" PORT.defl="COM4"
    export function beginPort(parameter: any, block: any) {
        const port = parameter.PORT.code;
        addImports();
        Generator.addCode(`board = Board.begin(BoardType.STARCORE_V2, port=${port})`);
    }

    //% block="---"
    export function separatorConnection() {
    }

    //% block="设置引脚 [PIN] 模式为 [MODE]" blockType="command"
    //% PIN.shadow="dropdown" PIN.options="PIN" PIN.defl="PIN.P0"
    //% MODE.shadow="dropdown" MODE.options="PIN_MODE" MODE.defl="PIN_MODE.OUTPUT"
    export function pinMode(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        const mode = parameter.MODE.code;
        addImports();
        Generator.addCode(`board.pin_mode(${pin}, ${mode})`);
    }

    //% block="数字写入 引脚 [PIN] 值 [VALUE]" blockType="command"
    //% PIN.shadow="dropdown" PIN.options="PIN" PIN.defl="PIN.P0"
    //% VALUE.shadow="dropdown" VALUE.options="DIGITAL_VALUE" VALUE.defl="DIGITAL_VALUE.HIGH"
    export function digitalWrite(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        const value = parameter.VALUE.code;
        addImports();
        Generator.addCode(`board.digital_write(${pin}, ${value})`);
    }

    //% block="数字读取 引脚 [PIN]" blockType="boolean"
    //% PIN.shadow="dropdown" PIN.options="PIN" PIN.defl="PIN.P0"
    export function digitalRead(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        addImports();
        Generator.addCode([`board.digital_read(${pin})`, Generator.ORDER_UNARY_POSTFIX]);
    }

    //% block="模拟读取 引脚 [PIN]" blockType="reporter"
    //% PIN.shadow="dropdown" PIN.options="ANALOG_PIN" PIN.defl="ANALOG_PIN.P0"
    export function analogRead(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        addImports();
        Generator.addCode([`board.analog_read(${pin})`, Generator.ORDER_UNARY_POSTFIX]);
    }

    //% block="模拟读取毫伏 引脚 [PIN]" blockType="reporter"
    //% PIN.shadow="dropdown" PIN.options="ANALOG_PIN" PIN.defl="ANALOG_PIN.P0"
    export function analogReadMillivolts(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        addImports();
        Generator.addCode([`board.analog_read(${pin}, millivolts=True)`, Generator.ORDER_UNARY_POSTFIX]);
    }

    //% block="DAC 输出 引脚 [PIN] 数值 [VALUE]" blockType="command"
    //% PIN.shadow="dropdown" PIN.options="DAC_PIN" PIN.defl="DAC_PIN.P9"
    //% VALUE.shadow="range" VALUE.params.min=0 VALUE.params.max=255 VALUE.defl=128
    export function analogWrite(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        const value = parameter.VALUE.code;
        addImports();
        Generator.addCode(`board.analog_write(${pin}, ${value})`);
    }

    //% block="---"
    export function separatorPwm() {
    }

    //% block="配置 PWM 引脚 [PIN] 频率 [FREQUENCY] Hz 分辨率 [RESOLUTION] 位" blockType="command"
    //% PIN.shadow="dropdown" PIN.options="OUTPUT_PIN" PIN.defl="OUTPUT_PIN.P0"
    //% FREQUENCY.shadow="number" FREQUENCY.defl=1000
    //% RESOLUTION.shadow="range" RESOLUTION.params.min=1 RESOLUTION.params.max=20 RESOLUTION.defl=8
    export function pwmConfigure(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        const frequency = parameter.FREQUENCY.code;
        const resolution = parameter.RESOLUTION.code;
        addImports();
        Generator.addCode(`board.pwm_configure(${pin}, ${frequency}, ${resolution})`);
    }

    //% block="PWM 写入 引脚 [PIN] 占空值 [DUTY]" blockType="command"
    //% PIN.shadow="dropdown" PIN.options="OUTPUT_PIN" PIN.defl="OUTPUT_PIN.P0"
    //% DUTY.shadow="number" DUTY.defl=128
    export function pwmWrite(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        const duty = parameter.DUTY.code;
        addImports();
        Generator.addCode(`board.pwm_write(${pin}, ${duty})`);
    }

    //% block="停止 PWM 引脚 [PIN]" blockType="command"
    //% PIN.shadow="dropdown" PIN.options="OUTPUT_PIN" PIN.defl="OUTPUT_PIN.P0"
    export function pwmStop(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        addImports();
        Generator.addCode(`board.pwm_stop(${pin})`);
    }

    //% block="---"
    export function separatorSensors() {
    }

    //% block="DHT11 引脚 [PIN] 温度（℃）" blockType="reporter"
    //% PIN.shadow="dropdown" PIN.options="DHT_PIN" PIN.defl="DHT_PIN.P1"
    export function dht11Temperature(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        addImports();
        Generator.addCode([`board.dht11(${pin}).read().temperature_c`, Generator.ORDER_UNARY_POSTFIX]);
    }

    //% block="DHT11 引脚 [PIN] 湿度（%）" blockType="reporter"
    //% PIN.shadow="dropdown" PIN.options="DHT_PIN" PIN.defl="DHT_PIN.P1"
    export function dht11Humidity(parameter: any, block: any) {
        const pin = parameter.PIN.code;
        addImports();
        Generator.addCode([`board.dht11(${pin}).read().humidity_percent`, Generator.ORDER_UNARY_POSTFIX]);
    }

    //% block="超声波 TRIG [TRIGGER] ECHO [ECHO] 距离（cm）" blockType="reporter"
    //% TRIGGER.shadow="dropdown" TRIGGER.options="OUTPUT_PIN" TRIGGER.defl="OUTPUT_PIN.P6"
    //% ECHO.shadow="dropdown" ECHO.options="INPUT_PIN" ECHO.defl="INPUT_PIN.P7"
    export function ultrasonicCm(parameter: any, block: any) {
        const trigger = parameter.TRIGGER.code;
        const echo = parameter.ECHO.code;
        addImports();
        Generator.addCode([`board.ultrasonic(${trigger}, ${echo}).read_cm()`, Generator.ORDER_UNARY_POSTFIX]);
    }

    //% block="---"
    export function separatorControl() {
    }

    //% block="复位星核板外设状态" blockType="command"
    export function resetState(parameter: any, block: any) {
        addImports();
        Generator.addCode(`board.reset_state()`);
    }

    //% block="关闭 StarBridge 连接" blockType="command"
    export function close(parameter: any, block: any) {
        addImports();
        Generator.addCode(`board.close()`);
    }

    function addImports() {
        Generator.addImport(`from starbridge_mindplus import Board, BoardType, Pin, PinMode`);
    }
}
